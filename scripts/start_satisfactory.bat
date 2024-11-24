@echo off
TITLE Start Satisfactory Server
echo Starting Satisfactory server...

:: Set the working directory to the Satisfactory server directory
cd /d "C:\Users\UserFolder\SteamCMD\steamapps\common\SatisfactoryDedicatedServer"

:: Start the server
start /min FactoryServer.exe -unattended -log

echo Satisfactory server started.
