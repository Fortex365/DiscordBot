#!/bin/bash

pid_file="$HOME/barmaid.pid"  # Corrected pid_file path

echo "Killing barmaid..."
pids=$(pgrep -f "python3 barmaid.py")

for pid in $pids; do
  sudo kill -9 "$pid"
done

echo "Updating barmaid libraries..."

cd ~/barmaid/

python3 -m pip install --upgrade yt_dlp

echo "Update successful"
