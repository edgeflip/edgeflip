#!/bin/bash
$VIRTUAL_ENV/bin/celery worker --app=edgeflip -l info -c4 -Q \
    px3,px3_filter,px4,celery
