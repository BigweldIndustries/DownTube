@echo off
echo "Checking Dependencies"
py -m pip install -r requirements.txt
echo "Running Python Application"
py main.py

echo "IF ERROR ON APP STARTUP, MAKE SURE ACTIVE DIRECTORY IS IN THE DOWNTUBE FOLDER BEFORE RASING A GITHUB ISSUE."