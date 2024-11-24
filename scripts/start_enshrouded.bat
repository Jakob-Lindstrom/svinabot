@echo off
TITLE Start Enshrouded Server
echo Starting Enshrouded server...

:: Set the working directory to the Enshrouded server directory
cd /d "C:\Users\UserFolder\SteamCMD\steamapps\common\EnshroudedServer"

:: Start the server
start /min enshrouded_server.exe

echo Enshrouded server started.
