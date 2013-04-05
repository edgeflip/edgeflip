#!/bin/bash
coverage erase
COVERAGE_PROCESS_START=.coveragerc coverage run -m unittest discover -b
coverage combine
coverage html
