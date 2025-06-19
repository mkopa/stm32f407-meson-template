# STM32F407VGT6 STM32CubeMX + Meson + Ninja

```bash
cp .env.dist .env
```
```bash
docker-compose build
```
```bash
docker-compose run --rm dev meson setup builddir --cross-file cross_file.docker.txt
```
```bash
docker-compose run --rm dev meson compile -C builddir
```
```bash
docker-compose run --rm dev ninja -C builddir flash
```
```bash
./rebuild.sh
```
```bash
./flash.sh
```

## Disclaimer: For Educational Purposes Only

The code and materials in this repository are provided solely for educational and demonstration purposes. They are not intended for, and should not be used for, any commercial, professional, or production-grade applications.

By using the contents of this repository, you agree that you will not use them for any commercial purposes. The author(s) provide no warranty of any kind and are not liable for any damages or losses arising from the use of this code.
