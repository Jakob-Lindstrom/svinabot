# config.py

import yaml

# Load configurations from YAML file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

DISCORD_TOKEN = config['discord']['token']
PASSWORD = config['password']
INITIAL_EXTENSIONS = ['cogs.games']
