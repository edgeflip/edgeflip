#!/bin/bash
python -m unittest discover -b
sphinx-build -b doctest -d doc/_build/doctrees doc doc/_build/doctest


