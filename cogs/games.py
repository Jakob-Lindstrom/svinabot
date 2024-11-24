import discord
from discord.ext import commands
from game_servers.base import GameServer
from config import config, PASSWORD
import logging
import asyncio
import subprocess
import os
import psutil
import win32gui
import win32con
from utils.server_info import get_external_ip, get_cpu_usage, get_memory_usage


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        # Initialize GameServer instances for each game
        for game_key, game_config in config['games'].items():
            required_keys = ['display_name', 'start_command', 'stop_command', 'process_name', 'startup_time']
            missing_keys = [key for key in required_keys if key not in game_config]
            if missing_keys:
                logging.error(f"Missing keys {missing_keys} in config for game '{game_key}'. Skipping initialization.")
                continue
            self.games[game_key.lower()] = GameServer(
                name=game_key.lower(),
                display_name=game_config['display_name'],
                start_command=game_config['start_command'],
                stop_command=game_config['stop_command'],
                update_command=game_config.get('update_command'),
                process_name=game_config['process_name'],
                update_log=game_config.get('update_log'),
                startup_time=game_config.get('startup_time', 30),
                shutdown_time=game_config.get('shutdown_time', 10)
            )
            logging.info(f"Initialized GameServer for '{game_key}' with startup_time={game_config.get('startup_time', 30)} seconds.")
            
    def _find_window_by_title_substring(self, substring):
            """Find the window handle for a window whose title contains the given substring."""
            hwnds = []

            def _window_enum_callback(hwnd, _):
                window_title = win32gui.GetWindowText(hwnd)
                if substring.lower() in window_title.lower():
                    hwnds.append(hwnd)

            win32gui.EnumWindows(_window_enum_callback, None)
            return hwnds[0] if hwnds else None

    async def run_bat_file_and_capture_output(self, command, log_file=None):
        """Helper function to run .bat files and capture output."""
        try:
            # Normalize the command path for consistent usage
            command = os.path.normpath(command)
            working_dir = os.path.dirname(command)

            # Log the resolved path for debugging
            logging.info(f"Attempting to run: {command}")

            # Run the batch file and capture output
            if log_file:
                # Ensure log directory exists
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                log_file_handle = open(log_file, 'w', encoding='utf-8')
                process = subprocess.Popen(
                    command,
                    cwd=working_dir,
                    shell=True,
                    stdout=log_file_handle,
                    stderr=subprocess.STDOUT
                )
            else:
                process = subprocess.Popen(
                    command,
                    cwd=working_dir,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            logging.info(f"Started process PID: {process.pid}")

            # Return the process object for monitoring
            return 0, "", "", process
        except Exception as e:
            logging.error(f"Error running command {command}: {e}")
            return -1, "", str(e), None



    async def run_bat_file(self, command):
        """Helper function to run .bat files without capturing output."""
        try:
            # Normalize the command path for consistent usage
            command = os.path.normpath(command)
            working_dir = os.path.dirname(command)

            # Log the resolved path for debugging
            logging.info(f"Attempting to run: {command}")

            # Run the batch file without waiting for it to finish
            subprocess.Popen(
                command,
                cwd=working_dir,
                shell=True
            )

            logging.info(f"Successfully started {command}")
            return 0, "", ""
        except Exception as e:
            logging.error(f"Error running command {command}: {e}")
            return -1, "", str(e)
            


# START COMMAND  

    @commands.command()
    async def start(self, ctx, game_name: str):
        """Starts the specified game server."""
        game = self.games.get(game_name.lower())
        if game and game.start_command:
            # Check if any other server is running
            running_games = [g for g in self.games.values() if g.is_running()]
            if running_games:
                running_game_names = ", ".join([g.display_name for g in running_games])
                await ctx.send(
                    f"❌ Cannot start {game.display_name} server because the following server(s) are already running: {running_game_names}. "
                    f"Please stop them before starting a new server."
                )
                return

            if game.is_running():
                await ctx.send(f"✅ {game.display_name} server is already running.")
                return

            # Send initial message
            message = await ctx.send(f"Starting {game.display_name} server...")

            # Start the server asynchronously
            returncode, stdout, stderr = await self.run_bat_file(game.start_command)
            
            # Retrieve the startup time from config
            startup_time = game.startup_time

            # Simulate progress
            progress_steps = 10
            sleep_per_step = startup_time / progress_steps
            for i in range(progress_steps):
                progress_bar = '🟩' * (i + 1) + '⬜' * (progress_steps - i - 1)
                progress_percent = int(((i + 1) / progress_steps) * 100)
                await message.edit(content=f"Starting {game.display_name} server...\nProgress: {progress_percent}%\n[{progress_bar}]")
                await asyncio.sleep(sleep_per_step)  # Use sleep_per_step instead of fixed 1 second

            # Check if the server started successfully
            if game.is_running():
                await message.edit(content=f"✅ {game.display_name} server started successfully!")
            else:
                await message.edit(
                    content=f"❌ Failed to start {game.display_name} server.\nError: {stderr}\nPlease check the logs for details."
                )
        else:
            await ctx.send(f"❌ Game '{game_name}' not found or start command not configured.")
            


# STOP COMMAND

    @commands.command()
    async def stop(self, ctx, game_name: str):
        """Stops the specified game server."""
        game = self.games.get(game_name.lower())
        if not game:
            await ctx.send(f"❌ Game '{game_name}' not found.")
            return

        if not game.is_running():
            await ctx.send(f"❌ {game.display_name} server is not running.")
            return

        # Send initial message
        message = await ctx.send(f"Stopping {game.display_name} server...\nProgress: 0%\n[⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜]")

        try:
            # Find the window using part of its title (process_name as substring)
            hwnd = self._find_window_by_title_substring(game.process_name)

            if hwnd:
                # Send WM_CLOSE to gracefully close the window
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

                # Set number of progress steps to 10
                progress_steps = 10
                sleep_per_step = game.shutdown_time / progress_steps

                # Wait for graceful shutdown with progress update
                for i in range(progress_steps):
                    progress_bar = '🟥' * (i + 1) + '⬜' * (progress_steps - i - 1)
                    progress_percent = int(((i + 1) / progress_steps) * 100)
                    await message.edit(content=f"Stopping {game.display_name} server...\nProgress: {progress_percent}%\n[{progress_bar}]")
                    await asyncio.sleep(sleep_per_step)

                # Check if the process is still running
                if game.is_running():
                    await ctx.send(f"⚠️ {game.display_name} server did not shut down gracefully in {game.shutdown_time} seconds. Forcing shutdown...")

                    # Use psutil to forcefully terminate the process
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'].lower() == game.process_name.lower():
                            proc.kill()  # Force kill the process
                            await ctx.send(f"❌ {game.display_name} server was forcefully shut down.")
                            break
                else:
                    await message.edit(content=f"✅ {game.display_name} server shut down successfully!")

            else:
                await ctx.send(f"❌ Could not find window for {game.display_name}. Please ensure the process is running and has a visible window.")

        except Exception as e:
            await message.edit(content=f"❌ Error stopping {game.display_name} server: {e}")

# RESTART COMMAND

    @commands.command()
    async def restart(self, ctx, game_name: str):
        """Restarts the specified game server."""
        game = self.games.get(game_name.lower())
        if not game:
            await ctx.send(f"❌ Game '{game_name}' not found.")
            return

        # Check if the game server is running
        if not game.is_running():
            await ctx.send(f"❌ {game.display_name} server is not running, so it cannot be restarted.")
            return

        # Send initial message
        message = await ctx.send(f"Restarting {game.display_name} server...\nStage: Shutting down...")

        # Stop the server gracefully with progress bar
        try:
            # Find the window using part of its title (process_name as substring)
            hwnd = self._find_window_by_title_substring(game.process_name)

            if hwnd:
                # Send WM_CLOSE to gracefully close the window
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

                # Set number of progress steps to 10
                shutdown_steps = 10
                sleep_per_step = game.shutdown_time / shutdown_steps

                # Wait for graceful shutdown with progress update
                for i in range(shutdown_steps):
                    progress_bar = '🟥' * (i + 1) + '⬜' * (shutdown_steps - i - 1)
                    progress_percent = int(((i + 1) / shutdown_steps) * 100)
                    await message.edit(content=f"Shutting down {game.display_name} server...\nProgress: {progress_percent}%\n[{progress_bar}]")
                    await asyncio.sleep(sleep_per_step)

                # Check if the process is still running
                if game.is_running():
                    await ctx.send(f"⚠️ {game.display_name} server did not shut down gracefully in {game.shutdown_time} seconds. Forcing shutdown...")

                    # Use psutil to forcefully terminate the process
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'].lower() == game.process_name.lower():
                            proc.kill()  # Force kill the process
                            await ctx.send(f"❌ {game.display_name} server was forcefully shut down.")
                            break
                else:
                    await message.edit(content=f"✅ {game.display_name} server shut down successfully!")

            else:
                await ctx.send(f"❌ Could not find window for {game.display_name}. Please ensure the process is running and has a visible window.")
                return

        except Exception as e:
            await message.edit(content=f"❌ Error stopping {game.display_name} server: {e}")
            return

        # Start the server with progress bar
        await message.edit(content=f"Restarting {game.display_name} server...\nStage: Starting up...")

        startup_steps = 10
        sleep_per_step = game.startup_time / startup_steps

        # Run the startup command asynchronously
        returncode, stdout, stderr = await self.run_bat_file(game.start_command)

        # Simulate startup progress
        for i in range(startup_steps):
            progress_bar = '🟩' * (i + 1) + '⬜' * (startup_steps - i - 1)
            progress_percent = int(((i + 1) / startup_steps) * 100)
            await message.edit(content=f"Starting {game.display_name} server...\nProgress: {progress_percent}%\n[{progress_bar}]")
            await asyncio.sleep(sleep_per_step)

        # Check if the server started successfully
        if game.is_running():
            await message.edit(content=f"✅ {game.display_name} server restarted successfully!")
        else:
            await message.edit(content=f"❌ Failed to start {game.display_name} server after shutdown.")





# STATUS COMMAND

    @commands.command()
    async def status(self, ctx):
        """Displays the status of all game servers."""
        embed = discord.Embed(title="🖥️ Server Status", color=discord.Color.blue())

        for game in self.games.values():
            # Determine the status indicator
            status_emoji = ":green_circle:" if game.is_running() else ":red_circle:"
            field_name = f"{status_emoji} {game.display_name}"
            field_value = "\u200b"
            embed.add_field(name=field_name, value=field_value, inline=False)

        # Add system information
        external_ip = get_external_ip()
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()

        embed.add_field(name="🌐 External IP", value=external_ip, inline=True)
        embed.add_field(name="🔐 Password", value=PASSWORD, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="🧠 CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="💾 Memory Usage", value=memory_usage, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        await ctx.send(embed=embed)


# UPDATE COMMAND

    @commands.command()
    async def update(self, ctx, game_name: str):
        """Updates the specified game server."""
        game = self.games.get(game_name.lower())
        if game and game.update_command:
            if game.is_running():
                await ctx.send(f"❌ Cannot update {game.display_name} server because it is currently running. Please stop the server before updating.")
                return

            # Send initial message
            message = await ctx.send(f"Updating {game.display_name} server...\nStage: Initializing...")

            # Start the update process
            returncode, stdout, stderr, process = await self.run_bat_file_and_capture_output(game.update_command, log_file=game.update_log)

            log_file = game.update_log
            update_finished = False
            final_message_set = False  # Track if final message has been sent

            # Open the log file in read mode and continuously read from it
            try:
                with open(log_file, 'r') as f:
                    # Go to the end of the file
                    f.seek(0, os.SEEK_END)

                    current_stage = "Initializing"

                    while not update_finished:
                        # Read new lines
                        line = f.readline()

                        if not line:
                            # If no new line, wait a bit and try again
                            await asyncio.sleep(1)
                            continue

                        line = line.strip().lower()

                        # Detect downloading stage
                        if "update state (0x61) downloading" in line:
                            current_stage = "Downloading"
                            try:
                                progress_text = line.split("progress:")[1].strip()
                                progress_percent = float(progress_text.split()[0])  # Extract the percentage value
                            except (ValueError, IndexError):
                                progress_percent = 0

                            progress_bar = '🟦' * int(progress_percent // 10) + '⬜' * (10 - int(progress_percent // 10))
                            await message.edit(content=f"{current_stage} {game.display_name} server...\nProgress: {progress_percent:.2f}%\n[{progress_bar}]")

                        # Detect verifying install stage
                        elif "update state (0x5) verifying install" in line:
                            current_stage = "Verifying Install"
                            try:
                                progress_text = line.split("progress:")[1].strip()
                                progress_percent = float(progress_text.split()[0])  # Extract the percentage value
                            except (ValueError, IndexError):
                                progress_percent = 0

                            progress_bar = '🟩' * int(progress_percent // 10) + '⬜' * (10 - int(progress_percent // 10))
                            await message.edit(content=f"{current_stage} {game.display_name} server...\nProgress: {progress_percent:.2f}%\n[{progress_bar}]")

                        # Detect verifying update stage (0x81)
                        elif "update state (0x81) verifying update" in line:
                            current_stage = "Verifying Update"
                            try:
                                progress_text = line.split("progress:")[1].strip()
                                progress_percent = float(progress_text.split()[0])  # Extract the percentage value
                            except (ValueError, IndexError):
                                progress_percent = 0

                            progress_bar = '🟧' * int(progress_percent // 10) + '⬜' * (10 - int(progress_percent // 10))
                            await message.edit(content=f"{current_stage} {game.display_name} server...\nProgress: {progress_percent:.2f}%\n[{progress_bar}]")

                        # Detect reconfiguring stage
                        elif "update state (0x3) reconfiguring" in line:
                            current_stage = "Reconfiguring"
                            await message.edit(content=f"{current_stage} {game.display_name} server...")

                        # Detect preallocating stage (0x11)
                        elif "update state (0x11) preallocating" in line:
                            current_stage = "Preallocating"
                            try:
                                progress_text = line.split("progress:")[1].strip()
                                progress_percent = float(progress_text.split()[0])  # Extract the percentage value
                            except (ValueError, IndexError):
                                progress_percent = 0

                            progress_bar = '🟨' * int(progress_percent // 10) + '⬜' * (10 - int(progress_percent // 10))
                            await message.edit(content=f"{current_stage} {game.display_name} server...\nProgress: {progress_percent:.2f}%\n[{progress_bar}]")

                        # Detect committing stage
                        elif "update state (0x101) committing" in line:
                            current_stage = "Committing"
                            try:
                                progress_text = line.split("progress:")[1].strip()
                                progress_percent = float(progress_text.split()[0])  # Extract the percentage value
                            except (ValueError, IndexError):
                                progress_percent = 0

                            progress_bar = '🟥' * int(progress_percent // 10) + '⬜' * (10 - int(progress_percent // 10))
                            await message.edit(content=f"{current_stage} {game.display_name} server updates...\nProgress: {progress_percent:.2f}%\n[{progress_bar}]")

                        # Detect completion
                        if "success! app" in line:
                            if "already up to date" in line:
                                await message.edit(content=f"✅ {game.display_name} server is already up to date!")
                            else:
                                await message.edit(content=f"✅ {game.display_name} server updated successfully!")
                            update_finished = True
                            final_message_set = True

                    # Check if process has completed without further output
                    if process.poll() is not None and not final_message_set:
                        await message.edit(content=f"✅ {game.display_name} server update process completed.")
                        update_finished = True

            except Exception as e:
                logging.error(f"Error while updating {game.display_name}: {e}")

        else:
            await ctx.send(f"❌ Game '{game_name}' not found or update command not configured.")





async def setup(bot):
    await bot.add_cog(GameCommands(bot))
