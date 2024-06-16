"""
Application configuration.
"""

import os
import toml
from default_config import CONST_DEFAULT_CONFIG

combined_config = {}


def initialize_config():
    "Merges configuration from config.toml with defaults."
    global combined_config

    config_file_path = os.path.join(os.getcwd(), "config.toml")

    with open(config_file_path) as f:
        data = toml.load(f)
        combined_config = {
            "system": CONST_DEFAULT_CONFIG["system"] | data["system"],
        }


def get_config() -> dict:
    "Returns app configuration as a dictionary."
    return combined_config


initialize_config()
