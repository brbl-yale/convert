#!/bin/bash
# Cron wrapper for convert.py

SOURCE="/some/path"
DESTINATION="/some/path/`date +%Y%m%d`"
THREADS="16"
# We'll use the defaults for the other variables
PYTHON="/usr/bin/python"

echo $PYTHON convert.py --source=$SOURCE --destination=$DESTINATION --threads=$THREADS

exec $PYTHON convert.py --source=$SOURCE --destination=$DESTINATION --threads=$THREADS 
