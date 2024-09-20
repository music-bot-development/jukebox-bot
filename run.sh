#!/bin/bash
echo "Updating package lists..."
sudo apt-get update

echo "Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-pip

echo "Installing requirements from requirements.txt..."
pip3 install -r requirements.txt

echo "Running main.py..."
python3 main.py

echo "Script execution completed."
