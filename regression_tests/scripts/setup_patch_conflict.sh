#!/bin/bash
# Script to set up patch conflict scenario
# This modifies the file during test run to cause conflicts

sleep 2  # Wait for Nova to start
echo "# Modified by conflict script" >> src/data_processor.py
