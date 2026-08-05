"""
Structured Logger: Centralized logging configuration for the platform.
Provides consistent log formatting with timestamps and module names
for all agents, services, and execution components.
"""
import logging
import sys
from pathlib import Path

def get_logger(name: str = "agentic_platform") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger
