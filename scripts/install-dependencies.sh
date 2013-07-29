#!/bin/bash
depfile="$(dirname ${0})/../dependencies/base.dependencies"

for f in $(<$depfile ); do
    sudo apt-get install -y "${f}"
done
