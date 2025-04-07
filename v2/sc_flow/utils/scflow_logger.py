# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import logging

def configure_logging(log_level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    log_format = 'SCFLOW - %(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(console_handler)