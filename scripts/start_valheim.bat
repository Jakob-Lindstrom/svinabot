@echo off
TITLE Valheim Server
set SteamAppId=892970
echo "Starting Valheim server..."

cd "C:\Users\UserFolder\SteamCMD\steamapps\common\Valheim dedicated server"

REM Start the server and minimize the window
start /min valheim_server.exe -nographics -batchmode -name "ServerName" -port 2456 -world "WorldName" -password "Password" -crossplay

echo Valheim server started.
