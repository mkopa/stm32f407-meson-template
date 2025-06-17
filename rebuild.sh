#!/bin/bash

rm -rf builddir
docker-compose build
#docker-compose run --rm dev python3 ./convert_to_meson.py Makefile 
docker-compose run --rm dev meson setup builddir --cross-file cross_file.docker.txt
docker-compose run --rm dev meson compile -C builddir