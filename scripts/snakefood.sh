#!/bin/bash
sfood --internal ${1} | sfood-graph | dot -Tps | ps2pdf - snakefood.pdf

