#!/bin/bash
depfile="$(dirname ${0})/../dependencies.txt"

for f in $(<$depfile ); do
    sudo apt-get install -y "${f}"
done
