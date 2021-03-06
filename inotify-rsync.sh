#!/bin/bash
# Copyright © 2016 Martin Ueding <dev@martin-ueding.de>

set -e
set -u
set -x

files=(*.py *.sh)

while true
do
    inotifywait -e modify,attrib,close_write,move,create,delete "${files[@]}" && \
        rsync -avhE "${files[@]}" juqueen:
done
