@echo off
TITLE Start Sons of the Forest Server
echo "Starting Sons of the Forest server..."

REM Ensure the working directory is set to the Sons of the Forest server folder
cd "C:\Users\UserFolder\SteamCMD\steamapps\common\Sons Of The Forest Dedicated Server"

REM Create the app ID file
echo|set /p="1326470" > steam_appid.txt
set SteamAppId=1326470

REM Start the Sons of the Forest server
start /min SonsOfTheForestDS.exe
