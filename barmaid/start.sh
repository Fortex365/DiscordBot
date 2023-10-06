#!/bin/bash

screen -wipe

cd ~/barmaid/

echo "Starting barmaid..."

# Run the Python script in a screen session and get the Python script's PID
screen -dmS barmaid_session bash -c 'python3 barmaid.py & echo $! > ~/barmaid.pid'

# Get the PID of the Python script from barmaid.pid
python_pid=$(cat ~/barmaid.pid)

echo "Barmaid started. Python script PID saved in barmaid.pid: $python_pid"