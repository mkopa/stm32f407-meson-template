project('DevEBox-STM324XX', 'c', 'cpp')

sources = files(
    'Core/Src/main.c',
    'Core/Src/stm32f4xx_it.c',
    'Core/Src/stm32f4xx_hal_msp.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rtc.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rtc_ex.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rcc.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rcc_ex.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash_ex.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash_ramfunc.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_gpio.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma_ex.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_pwr.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_pwr_ex.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_cortex.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal.c',
    'Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_exti.c',
    'Core/Src/system_stm32f4xx.c'
)

asm_sources = files('startup_stm32f407xx.s')

inc_dirs = include_directories(
    'Core/Inc',
    'Drivers/STM32F4xx_HAL_Driver/Inc',
    'Drivers/STM32F4xx_HAL_Driver/Inc/Legacy',
    'Drivers/CMSIS/Device/ST/STM32F4xx/Include',
    'Drivers/CMSIS/Include'
)

c_defs = [
  '-DSTM32F407xx',
  '-DUSE_HAL_DRIVER'
]
add_project_arguments(c_defs, language: ['c', 'cpp'])

linker_script_file = 'STM32F407XX_FLASH.ld'
linker_script_dep = files(linker_script_file)

project_link_args = [
  '-T', join_paths(meson.project_source_root(), linker_script_file)
]

fw_elf = executable(
    meson.project_name() + '.elf',
    sources,
    asm_sources,
    include_directories: inc_dirs,
    link_args: project_link_args,
    link_depends: linker_script_dep
)

# --- Post-Build Steps ---
objcopy = find_program('arm-none-eabi-objcopy')
size_tool = find_program('arm-none-eabi-size')

fw_bin = custom_target(
  meson.project_name() + '_bin',
  input: fw_elf,
  output: meson.project_name() + '.bin',
  command: [objcopy, '-O', 'binary', '@INPUT@', '@OUTPUT@'],
  build_by_default: true
)

fw_hex = custom_target(
  meson.project_name() + '_hex',
  input: fw_elf,
  output: meson.project_name() + '.hex',
  command: [objcopy, '-O', 'ihex', '@INPUT@', '@OUTPUT@'],
  build_by_default: true
)

run_target(
  'size',
  command: [size_tool, '--format=berkeley', fw_elf]
)

openocd = find_program('openocd', required: false)
if openocd.found()
  run_target(
    'flash',
    command: [
      openocd,
      '-f', 'interface/stlink.cfg',
      '-f', 'target/stm32f4x.cfg',
      '-c', 'program ' + fw_elf.full_path() + ' verify reset exit'
    ],
    depends: fw_elf
  )
endif