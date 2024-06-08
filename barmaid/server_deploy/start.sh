#!/bin/bash

screen -wipe

cd ~/barmaid/

echo "Starting barmaid..."

# Create a new screen session named "barmaid_session" and run the Python script in it
screen -dmS barmaid_session python3 barmaid.py

# Save the screen session's PID to a file named "screen_session.pid"
screen_pid=$(screen -list | grep "barmaid_session" | cut -f1 -d'.' | awk '{print $1}')
echo $screen_pid > ~/screen_session.pid

# Get the PID of the python3 barmaid.py process and save it to "barmaid.pid"
python_pid=$(pgrep -f "python3 barmaid.py")
echo $python_pid > ~/barmaid.pid

echo "Barmaid started. Screen session PID saved in screen_session.pid. Python script PID saved in barmaid.pid."