# game_servers/base.py

import psutil

class GameServer:
    def __init__(
        self,
        name,
        display_name,
        start_command,
        stop_command,
        update_command,
        process_name,
        update_log,
        startup_time=10,  
        shutdown_time=10  
    ):
        self.name = name
        self.display_name = display_name
        self.start_command = start_command
        self.stop_command = stop_command
        self.update_command = update_command
        self.process_name = process_name
        self.update_log = update_log
        self.startup_time = startup_time  
        self.shutdown_time = shutdown_time  
        self.process = None  

    def is_running(self):
        """Check if the server process is running."""
        
        if self.process and self.process.poll() is None:
            return True

        
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmdline_list = proc.info.get('cmdline', [])
                if cmdline_list and isinstance(cmdline_list, list):
                    cmdline = ' '.join(cmdline_list).lower()
                else:
                    cmdline = ''

                if self.process_name.lower() in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
