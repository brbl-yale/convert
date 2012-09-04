#!/bin/bash
# Cron wrapper for convert.py

SOURCE="/Users/brblsys/Documents/PROCESS"
DESTINATION="/Users/brblsys/Documents/DONE"
THREADS="16"
# We'll use the defaults for the other variables
PYTHON="/usr/bin/python"

exec PYTHON convert.py --source=$SOURCE --destination=$DESTINATION --threads=$THREADS
