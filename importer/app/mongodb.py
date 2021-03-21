#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------------------
# Connect to MongoDB and return the client                                              -
# ---------------------------------------------------------------------------------------

import pymongo, logging, config, time
from logging.config import fileConfig

class Mongodb:

    client = ""
    
    def __init__(self) -> None:
        # set up logging
        fileConfig(config.env.LOGGING_CONFIG_FILE)

    def connect(self, DB_URI):

        logging.info("Connecting to DB...")
    
        while(True):
            
            try:
                self.client = pymongo.MongoClient(DB_URI)
                db = self.client.binance
                status = db.command("serverStatus")
                logging.info("Running MongoDB version {}".format(status.get('version')))
                return self.client
            except Exception as error:
                logging.error(error)

            time.sleep(1)

    def close(self):
        self.client.close()