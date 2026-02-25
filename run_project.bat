@echo off
TITLE Secure Feedback System - Starter
echo [1/3] Starting Ganache in a new terminal...
start cmd /k "npx ganache --seed 1234"

echo Waiting for Ganache to initialize (5s)...
timeout /t 5 /nobreak > NUL

echo [2/3] Deploying Smart Contract...
python deploy.py

echo [3/3] Starting Flask Application...
python app.py

pause
