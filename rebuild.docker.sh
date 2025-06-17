#!/bin/bash

rm -rf builddir
docker-compose build
docker-compose run --rm dev meson setup builddir --cross-file cross_file.docker.txt
docker-compose run --rm dev meson compile -C builddir