# utils/server_info.py

import requests
import psutil

def get_external_ip():
    try:
        res = requests.get('https://api.ipify.org')
        res.raise_for_status()
        return res.text
    except requests.RequestException:
        return 'Unable to fetch IP'

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    mem = psutil.virtual_memory()
    used_memory_gb = mem.used / (1024 ** 3)
    total_memory_gb = mem.total / (1024 ** 3)
    return f"{used_memory_gb:.1f} GB / {total_memory_gb:.1f} GB"
