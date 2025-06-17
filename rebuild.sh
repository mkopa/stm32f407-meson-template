#!/bin/bash

rm -rf builddir
meson setup builddir --cross-file cross_file.txt
meson compile -C builddir