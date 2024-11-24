# utils/logger.py

import logging
import os

def setup_logger():
    log_directory = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_directory, "bot.log"), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
