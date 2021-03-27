#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------------------
# Download historical data for every symbol and every defined channel                   -
# https://sammchardy.github.io/binance/2018/01/08/historical-data-download-binance.html -
# ---------------------------------------------------------------------------------------

# Imports
import logging, pymongo, config, mongodb
from datetime import datetime
from binance.helpers import date_to_milliseconds
from time import sleep, time
from binance.client import Client
from pytimeparse.timeparse import timeparse
from logging.config import fileConfig

# Functions
def to_datetime(ts):
    return datetime.fromtimestamp(ts / 1000)

def count_bars(stream_type):
    return db.binance.data.count_documents(
        filter={"stream_type": stream_type},
    )

# call main function
if __name__ == "__main__":

    # set up logging
    fileConfig(config.env.LOGGING_CONFIG_FILE)

    while(True):

        # connect to the db
        mongodbClass = mongodb.Mongodb()
        db = mongodbClass.connect(config.env.DB_URI)

        # connect to Binance
        logging.info("Connecting to Binance API...")
        binance = Client()

        # get history start date
        history_start_date = config.env.HISTORY_START_DATE

        # get all stream_types and channels
        stream_types = []
        channels = config.env.HISTORY_CHANNELS.split(', ')
        while(True):

            symbols = db.binance.symbols.distinct("symbol")

            if len(symbols) > 0:

                for symbol in symbols:
                    for channel in channels:
                        stream_types.append(f"{symbol.lower()}@{channel}")

                break

            else:

                logging.info(f"Could not get history because the symbols table seems to be empty. Retring in 5 seconds")
                sleep(5)

        logging.info(f"Getting history data starting from {history_start_date} for {len(stream_types)} stream types")

        # process all stream types present in the DB
        i = 1
        for stream_type in stream_types:

            logging.info(f"------------- {i} of {len(stream_types)} -------------")
            logging.info(f"Analyzing {stream_type}")
            i += 1

            # variables
            start_date = history_start_date
            start_date_dt = datetime.fromisoformat(history_start_date)
            start_date_unix = start_date_dt.timestamp()

            # get symbol and interval
            try:
                symbol, type = stream_type.split('@', 1)
                interval_string = type.split('_', 1)[1]
                interval = timeparse(interval_string)
            except Exception as e:
                logging.error(f"Could not parse symbol or interval for {stream_type}. Error: {e}")
                continue

            # check the last checkpoint
            result = db.binance.checkpoints.find_one(
                filter={"stream_type": stream_type}
            )

            if result and result.get("time"):
                start_date_unix = result.get("time")
                start_date = datetime.utcfromtimestamp(start_date_unix).strftime('%Y-%m-%d %H:%M:%S')
                logging.info(f'Checkpoint for {stream_type} found "{start_date}"')

            # getting history data from API
            start_time = time()
            now_seconds = int(time())

            if (now_seconds - start_date_unix) > interval:

                try:
                    bars = binance.get_historical_klines(
                        symbol.upper(), interval_string, start_date, limit=1000
                    )
                except Exception as e:
                    logging.error(f"Error while getting data from Binance for {stream_type}: {e}")
                    continue

            else:

                logging.info(f"{stream_type} history is complete")
                continue

            logging.info(f"[{int((time() - start_time))} s] {len(bars)} bar(s) for {stream_type} fetched")

            # formatting and inserting to DB
            try:

                start_time = time()

                requests = []
                for bar in bars:
                    
                    record = {}
                    record['stream_type'] =         stream_type
                    record['start_time'] =          bar[0]
                    record['close_time'] =          bar[6]
                    record['open_price'] =          bar[1]
                    record['close_price'] =         bar[4]
                    record['high_price'] =          bar[2]
                    record['low_price'] =           bar[3]
                    record['number_of_trades'] =    bar[8]

                    requests.append(pymongo.ReplaceOne(
                        {"stream_type": record.get('stream_type'),
                        "close_time": record.get('close_time')},
                        record, upsert=True))

                result = db.binance.data.bulk_write(requests)

                logging.info("[{} ms] [Missing records: {}] [Updated records: {}] for {}".format(
                    int((time() - start_time) * 1000), result.upserted_count, result.modified_count, stream_type))

                # save checkpoint
                bars_count = count_bars(stream_type)
                bars_expected = int((now_seconds - (date_to_milliseconds(history_start_date) / 1000)) / interval)
                bars_percent_complete = round(float(bars_count * 100 / bars_expected), 3)
                db.binance.checkpoints.update_one(
                    { 
                        "stream_type": stream_type
                    },
                    {
                        "$set": {
                            "time": now_seconds,
                            "stream_type": stream_type,
                            "bars_expected": bars_expected,
                            "bars_count": bars_count,
                            "bars_percent_complete": bars_percent_complete
                        }
                    }, 
                    upsert=True
                )

                logging.info(f"{stream_type} history complete at {bars_percent_complete}% (Count={bars_count}, Expected={bars_expected})")
            
            except Exception as e:
                    logging.error(e)

        # close connection to DB
        db.close()
         
        logging.info(f"Running history check again in {config.env.HISTORY_RUN_EVERY_MIN} minutes")
        sleep(int(config.env.HISTORY_RUN_EVERY_MIN) * 60)
