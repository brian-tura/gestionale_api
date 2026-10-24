@echo off
title BEE MANAGER CONTROL PANEL

cd /d "%~dp0"

echo Avvio Django Server...
start cmd /k "cd apicoltura && ..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000"

timeout /t 3

echo Avvio Tunnel Ngrok...
start cmd /k "ngrok http 8000"

echo.
echo ---------------------------------------------------
echo BEE MANAGER in funzione!
echo ---------------------------------------------------
echo Cartella: %CD%
echo.
echo Controlla la finestra di Ngrok per il link HTTPS.
echo ---------------------------------------------------
pause