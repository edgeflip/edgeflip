#!/bin/bash
depfile="$(dirname ${0})/../dependencies.txt"

for f in $(<$depfile ); do
    echo sudo apt-get install "${f}"
done
