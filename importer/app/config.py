#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------------------
# Load configuration from file and overwrite if defined in the environments variables   -
# ---------------------------------------------------------------------------------------

import sys, yaml, logging
from os import path, getenv
from box import Box
from logging.config import fileConfig

# get the absolute path where this script is located
absolute_path = path.dirname(path.abspath(__file__))
config_file = path.join(absolute_path, 'config.yaml')
logging_config_file = path.join(absolute_path, 'logging.ini')

# load config from yaml file
env = Box.from_yaml(filename=config_file, Loader=yaml.FullLoader)

# load logging config from ini file
fileConfig(logging_config_file)

# add config files path to the config (not editable through environemnt variables)
env['CONFIG_FILE'] = config_file
env['LOGGING_CONFIG_FILE'] = logging_config_file
env['PYTHON_VERSION'] = sys.version

# load config
logging.info("########## CONFIG ###########")

for key in env:
    # conf[key] = get_environment_variable(key, conf[key])
    env[key] = getenv(key, env[key])
    logging.info(f"{key} = {env[key]}")

logging.info("#############################")
