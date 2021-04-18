#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------
# Analyze cryptocurrencies                                                           -
# ------------------------------------------------------------------------------------

import config, logging
import pandas as pd
import numpy as np
from logging.config import fileConfig
from pymongo import MongoClient, UpdateOne
from time import sleep, time
from pytimeparse.timeparse import timeparse
# from datetime import date, timedelta

# call main function
if __name__ == "__main__":

    # set up logging
    fileConfig(config.env.LOGGING_CONFIG_FILE)

    db = MongoClient(config.env.DB_URI)

    while(True):

        # get all unique stream_types present in the DB
        while(True):

            result = db.binance.data.distinct("stream_type")
            stream_types = list(result)
            
            if len(stream_types) > 0:
                logging.info(f"{len(stream_types)} stream types found")
                break
            else:
                logging.info(f"Data table seems to be empty. Retring in 5 seconds")
                sleep(5)

        logging.info("Calculating Indicators")

        records = {}

        for stream_type in stream_types:

            # get interval
            try:
                symbol, type = stream_type.split('@', 1)
                interval_string = type.split('_', 1)[1]
                # interval = timeparse(interval_string)
            except:
                continue

            result = db.binance.data.find(
                filter={"stream_type": stream_type},
                projection={"_id": 0, "close_time": 1, "close_price": 1},
                sort=[('close_time', -1)],
                limit=config.env.ANALYZER_AMOUNT_CANDLES
            )

            ##################################
            ### Volatility ###################
            ##################################

            df = pd.DataFrame(result).astype({"close_time": np.int64, "close_price": np.float32})
            df['sma'] = df['close_price'].rolling(10).mean()
            df['volatility_percent'] = (1 - (df['close_price'] / df['close_price'].rolling(10).mean())).abs() * 100
            
            try:
                volatility = df['volatility_percent'].mean().round(1)
            except:
                volatility = 0

            # check if the symbol was alredy processed. If not define it in the dict
            try:
                records[symbol]['volatility'][interval_string] = 0
            except KeyError:
                records[symbol] = {}
                records[symbol]['volatility'] = {}

            records[symbol]['volatility'][interval_string] = volatility
          
        ##################################
        ### Update DB  ###################
        ##################################

        logging.info("Updating DB")

        requests = []
        for symbol in records:
            requests.append(UpdateOne(
                {
                    "symbol": symbol.upper()
                }, {
                    "$set": {
                        "volatility": records.get(symbol).get('volatility')
                    }
                }, 
                upsert=True)
            )

        start_time = time()
        result = db.binance.symbols.bulk_write(requests)
        logging.info("[{} ms] [Missing records: {}] [Updated records: {}]".format(
            int((time() - start_time) * 1000), result.upserted_count, result.modified_count))

        logging.info(f"Running analyzer again in {config.env.ANALYZER_RUN_EVERY_MIN} min")
        sleep(int(config.env.ANALYZER_RUN_EVERY_MIN) * 60)