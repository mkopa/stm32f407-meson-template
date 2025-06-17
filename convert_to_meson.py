#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import argparse
from pathlib import Path

def parse_makefile(makefile_path):
    """
    Parsuje plik Makefile wygenerowany przez STM32CubeMX i ekstrahuje kluczowe zmienne.
    """
    makefile_data = {}
    try:
        with open(makefile_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Obsługa zmiennej FLOAT-ABI, zamieniając ją na FLOAT_ABI
            content = content.replace('FLOAT-ABI', 'FLOAT_ABI')
    except FileNotFoundError:
        print(f"Błąd: Plik {makefile_path} nie został znaleziony.")
        return None

    # Zmienne jednoliniowe do sparsowania
    simple_vars = [
        'TARGET', 'CPU', 'FPU', 'FLOAT_ABI', 'MCU', 'DEBUG',
        'OPT', 'LDSCRIPT', 'PREFIX'
    ]
    for var in simple_vars:
        # Używamy \s* wokół =, aby obsłużyć różne formatowania
        match = re.search(rf'^{var}\s*=\s*(.*)', content, re.MULTILINE)
        if match:
            makefile_data[var] = match.group(1).strip()

    # Zmienne wieloliniowe (C_SOURCES, ASM_SOURCES, C_INCLUDES, C_DEFS, CPP_SOURCES)
    multi_line_vars = ['C_SOURCES', 'CPP_SOURCES', 'ASM_SOURCES', 'C_INCLUDES', 'C_DEFS']
    for var in multi_line_vars:
        # Regex do znalezienia bloku zmiennej wieloliniowej
        # Szuka bloku 'VAR = \' aż do następnej linii, która nie jest kontynuacją
        match = re.search(rf'^{var}\s*=\s*(?:\\\n)?(.*?)(?:\n\n|\n\w+\s*=|\Z)', content, re.DOTALL)
        if not match:  # Spróbuj dopasować jako zmienną jednoliniową
            match = re.search(rf'^{var}\s*=\s*(.*)', content, re.MULTILINE)

        if match:
            # Czyszczenie i podział wartości
            raw_values = match.group(1).strip()
            # Usuwamy znaki kontynuacji linii i dzielimy na poszczególne wpisy
            items = re.split(r'\s+|\\', raw_values)
            # Filtrujemy puste wpisy
            makefile_data[var] = [item for item in items if item]
        else:
            makefile_data[var] = [] # Zwróć pustą listę jeśli nie znaleziono

    # Parsowanie LDFLAGS i LIBS
    ldflags_match = re.search(r'^LDFLAGS\s*=\s*(.*)', content, re.MULTILINE)
    if ldflags_match:
        ldflags_str = ldflags_match.group(1)
        specs_match = re.search(r'(-specs=[\w.-]+)', ldflags_str)
        gc_sections_match = re.search(r'(-Wl,--gc-sections)', ldflags_str)
        makefile_data['LDFLAGS_SPECS'] = specs_match.group(0) if specs_match else None
        makefile_data['LDFLAGS_GC'] = gc_sections_match.group(0) if gc_sections_match else None

    libs_match = re.search(r'^LIBS\s*=\s*(.*)', content, re.MULTILINE)
    if libs_match:
        makefile_data['LIBS'] = libs_match.group(1).strip().split()
    else:
        makefile_data['LIBS'] = []

    return makefile_data

def generate_cross_file(data, toolchain_path=None):
    """
    Generuje zawartość pliku cross_file.txt na podstawie sparsowanych danych.
    """
    prefix = data.get('PREFIX', 'arm-none-eabi-')
    
    cpu = data.get('CPU', '').replace('-mcpu=', '')

    # Flagi architektury z MCU
    mcu_flags = data.get('MCU', '').split()

    # Budowanie listy flag kompilatora C
    c_args = mcu_flags[:]
    c_args.append(data.get('OPT', ''))
    if data.get('DEBUG') == '1':
        c_args.extend(['-g', '-gdwarf-2'])
    # UWAGA: C_DEFS są teraz obsługiwane w meson.build

    # Budowanie listy flag linkera
    link_args = mcu_flags[:]
    if data.get('LDFLAGS_SPECS'):
        link_args.append(data.get('LDFLAGS_SPECS'))
    if data.get('LDFLAGS_GC'):
        link_args.append(data.get('LDFLAGS_GC'))
    link_args.extend(data.get('LIBS', []))

    # Formatowanie list do stringa dla pliku Meson
    c_args_str = ',\n                '.join([f"'{arg}'" for arg in c_args if arg])
    link_args_str = ',\n                 '.join([f"'{arg}'" for arg in link_args if arg])

    # Generowanie ścieżek do binariów
    binaries = {
        tool: f"'{str(Path(toolchain_path) / (prefix + tool))}'" if toolchain_path else f"'{prefix}{tool}'"
        for tool in ['gcc', 'g++', 'ar', 'strip', 'objcopy', 'size']
    }

    content = f"""
[binaries]
c       = {binaries['gcc']}
cpp     = {binaries['g++']}
ar      = {binaries['ar']}
strip   = {binaries['strip']}
objcopy = {binaries['objcopy']}
size    = {binaries['size']}

[host_machine]
system      = 'none'
cpu_family  = 'arm'
cpu         = '{cpu}'
endian      = 'little'

[built-in options]
# Flagi dla kompilatora C. Obejmują flagi architektury i optymalizacje.
# Definicje preprocesora (-D) są zarządzane w meson.build
c_args = [{c_args_str}]

# Przykładowe flagi dla kompilatora C++. Dostosuj w razie potrzeby.
cpp_args = c_args + ['-fno-exceptions', '-fno-rtti']

# Flagi dla linkera. Skrypt linkera jest podawany osobno w meson.build.
c_link_args = [{link_args_str}]
cpp_link_args = c_link_args
"""
    return content.strip()

def generate_meson_build(data):
    """
    Generuje zawartość pliku meson.build na podstawie sparsowanych danych.
    """
    target_name = data.get('TARGET', 'firmware')
    
    # Sprawdzenie języków projektu
    languages = ['c']
    if data.get('CPP_SOURCES'):
        languages.append('cpp')
    languages_str = ", ".join([f"'{lang}'" for lang in languages])

    # Formatowanie źródeł
    c_sources_str = ',\n  '.join([f"'{s}'" for s in data.get('C_SOURCES', [])])
    asm_sources_str = ',\n  '.join([f"'{s}'" for s in data.get('ASM_SOURCES', [])])
    cpp_sources_str = ',\n  '.join([f"'{s}'" for s in data.get('CPP_SOURCES', [])])

    # Formatowanie ścieżek dołączanych
    includes = [inc.replace('-I', '') for inc in data.get('C_INCLUDES', [])]
    includes_str = ',\n  '.join([f"'{inc}'" for inc in includes])

    # Formatowanie definicji
    c_defs = data.get('C_DEFS', [])
    c_defs_str = ',\n  '.join([f"'{d}'" for d in c_defs])

    linker_script = data.get('LDSCRIPT', '')
    
    # Logika C++
    cpp_block = ""
    if cpp_sources_str:
        cpp_block = f"""
cpp_sources = files(
  {cpp_sources_str}
)
"""
    
    executable_sources = "sources, asm_sources"
    if cpp_sources_str:
        executable_sources += ", cpp_sources"


    content = f"""
project('{target_name}', [{languages_str}],
  default_options: [
    'b_lto=false',      # LTO może powodować problemy z debugowaniem
    'b_map=true',       # Automatycznie generuje plik .map
    'b_staticpic=false' # Ważne dla bare-metal
  ]
)

sources = files(
  {c_sources_str}
)

asm_sources = files(
  {asm_sources_str}
)
{cpp_block}
inc_dirs = include_directories(
  {includes_str}
)

# Definicje preprocesora przekazywane do kompilatora
project_defs = [
  {c_defs_str}
]
add_project_arguments(project_defs, language: [{languages_str}])

# Przygotowanie argumentów dla linkera, włączając skrypt linkera
linker_script_file = '{linker_script}'
linker_script_dep = files(linker_script_file)
# Argumenty linkera z cross_file.txt są dodawane automatycznie przez Meson.
# Tutaj dodajemy tylko te, które są specyficzne dla tego celu, czyli skrypt linkera.
project_link_args = ['-T', join_paths(meson.project_source_root(), linker_script_file)]

# Definicja pliku wykonywalnego .elf
elf_file = executable(
  meson.project_name() + '.elf',
  {executable_sources},
  include_directories: inc_dirs,
  link_args: project_link_args,
  link_depends: linker_script_dep
)

# --- Kroki po budowaniu ---
# Meson automatycznie użyje narzędzi zdefiniowanych w [binaries] w pliku cross_file
objcopy = find_program('objcopy')
size_tool = find_program('size')

# Cel do generowania pliku .bin z pliku .elf
custom_target(
    meson.project_name() + '.bin',
    input: elf_file,
    output: meson.project_name() + '.bin',
    command: [objcopy, '-O', 'binary', '@INPUT@', '@OUTPUT@'],
    build_by_default: true
)

# Cel do generowania pliku .hex z pliku .elf
custom_target(
    meson.project_name() + '.hex',
    input: elf_file,
    output: meson.project_name() + '.hex',
    command: [objcopy, '-O', 'ihex', '@INPUT@', '@OUTPUT@'],
    build_by_default: true
)

# Wyświetlanie rozmiaru firmware po kompilacji
run_target(
  'size',
  command: [size_tool, '--format=berkeley', elf_file]
)

# Opcjonalny cel do flashowania przez OpenOCD
openocd = find_program('openocd', required: false)
if openocd.found()
  run_target(
    'flash',
    command: [
      openocd,
      '-f', 'interface/stlink.cfg',        # Może wymagać dostosowania do Twojego debuggera
      '-f', 'target/stm32f4x.cfg',         # Może wymagać dostosowania do Twojego MCU
      '-c', 'program @INPUT@ verify reset exit'
    ],
    depends: elf_file
  )
endif
"""
    return content.strip()


def main():
    """
    Główna funkcja skryptu.
    """
    parser = argparse.ArgumentParser(
        description="Konwertuje projekt Makefile z STM32CubeMX na pliki Meson.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'makefile',
        type=str,
        help="Ścieżka do wejściowego pliku Makefile."
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help="Katalog wyjściowy dla plików meson.build i cross_file.txt (domyślnie bieżący)."
    )
    parser.add_argument(
        '--toolchain-path',
        type=str,
        help="Opcjonalna ścieżka do katalogu 'bin' toolchaina ARM (np. /usr/bin)."
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Parsowanie pliku {args.makefile}...")
    makefile_data = parse_makefile(args.makefile)
    if not makefile_data:
        return

    print("Generowanie pliku cross_file.txt...")
    cross_file_content = generate_cross_file(makefile_data, args.toolchain_path)
    cross_file_path = output_path / 'cross_file.txt'
    with open(cross_file_path, 'w', encoding='utf-8') as f:
        f.write(cross_file_content)
    print(f"Zapisano {cross_file_path}")

    print("Generowanie pliku meson.build...")
    meson_build_content = generate_meson_build(makefile_data)
    meson_build_path = output_path / 'meson.build'
    with open(meson_build_path, 'w', encoding='utf-8') as f:
        f.write(meson_build_content)
    print(f"Zapisano {meson_build_path}")

    print("\nKonwersja zakończona pomyślnie!")
    print("\nAby skonfigurować projekt, użyj polecenia (tylko raz):")
    print(f"  meson setup builddir --cross-file {cross_file_path.name}")
    print("\nAby zbudować projekt, użyj polecenia:")
    print("  meson compile -C builddir")
    print("\nAby wyświetlić rozmiar, użyj polecenia:")
    print("  meson compile -C builddir size")
    print("\nAby wgrać program na urządzenie (jeśli OpenOCD jest dostępny), użyj:")
    print("  meson compile -C builddir flash")


if __name__ == '__main__':
    main()
