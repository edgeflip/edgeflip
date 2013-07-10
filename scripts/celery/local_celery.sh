#!/bin/bash
$VIRTUAL_ENV/bin/celery worker --app=edgeflip -l info -Q user_info
