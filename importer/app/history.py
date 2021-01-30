#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------------------
# Check if there is missing data. If yes, download it                                   -
# https://sammchardy.github.io/binance/2018/01/08/historical-data-download-binance.html -
# ---------------------------------------------------------------------------------------

# Imports
import os
import logging
import pymongo
from datetime import datetime
from binance.helpers import date_to_milliseconds
from time import sleep, time
from binance.client import Client
from pytimeparse.timeparse import timeparse

# Functions
def load_config():
    ''' the configuration is loaded from the ENV variables.
        If they are not defined the default value specified here will be loaded '''

    global config
    config = {}

    logging.info("########## CONFIG ###########")
    set_variable('DB_URI', 'mongodb://crypto:Cr7ptopa55@localhost:27017')
    set_variable('HISTORY_START_DATE', '1 Jan, 2021 UTC')
    set_variable('HISTORY_INITIAL_DELAY_S', 1)
    set_variable('HISTORY_RUN_EVERY_MIN', 60)
    logging.info("#############################")

def set_variable(key, default):
    global config
    config[key] = os.getenv(key, default)
    logging.info("{}: {}".format(key, config[key]))

def connect_db():
    global db

    while(True):
        logging.info("Connecting to DB...")

        try:
            client = pymongo.MongoClient(config['DB_URI'])
            db = client.binance
            status = db.command("serverStatus")
            logging.info("Running MongoDB version {}".format(status.get('version')))
            break
        except Exception as error:
            logging.error(error)

def connect_binance():
    global client
    logging.info("Connecting to Binance API...")
    client = Client()

def to_datetime(ts):
    return datetime.fromtimestamp(ts / 1000)

# call main function
if __name__ == "__main__":

    # set up logging
    logging.basicConfig(format="%(asctime)s | %(levelname)s | %(module)s |  %(message)s",
                        level=os.getenv('LOG_LEVEL', 'INFO'),
                        datefmt="%Y-%m-%d %H:%M:%S")

    load_config()
    connect_db()
    connect_binance()

    # wait some time before checking history
    sleep(int(config['HISTORY_INITIAL_DELAY_S']))

    while(True):

        # get all unique symbols present in the DB and the start date for the history
        stream_types = db.data.distinct("stream_type")
        history_start_date = config['HISTORY_START_DATE']
        logging.info("Getting history data starting from {} for: {}".format(history_start_date, stream_types))

        # process all stream types present in the DB
        for stream_type in stream_types:

            # get interval
            symbol, type = stream_type.split('@', 1)
            interval_string = type.split('_', 1)[1]
            interval = timeparse(interval_string)

            history_end_date_ms = int(time() * 1000)

            # count actual entries present in the DB for the specified stream type
            count_entries = db.data.count_documents(
                filter={"stream_type": stream_type},
            )
            
            if count_entries > 0:

                # check if the present data is complete or has skipped some data
                result = db.data.find_one(
                    filter={"stream_type": stream_type},
                    projection={"_id": 0, "close_time": 1},
                    sort=[('close_time', -1)]
                )
                max_close_time = result.get('close_time')

                result = db.data.find_one(
                    filter={"stream_type": stream_type},
                    projection={"_id": 0, "close_time": 1},
                    sort=[('close_time', 1)]
                )
                min_close_time = result.get('close_time')

                difference = max_close_time - min_close_time

                expected_entries = int(difference / interval / 1000)

                if count_entries >= expected_entries * 0.999:
                    logging.info("Excluding period starting from {} to {} for {} because it is already complete".format(
                        to_datetime(min_close_time), to_datetime(max_close_time), stream_type
                    ))
                    history_end_date_ms = min_close_time
                else:
                    logging.info("{} has {} missing records".format(stream_type, expected_entries - count_entries))

            # missing entries
            missing_entries = int((history_end_date_ms - date_to_milliseconds(history_start_date)) / (interval * 1000))

            if missing_entries > 0:

                logging.info("{} missing entries for {}".format(missing_entries, stream_type))
                
                # getting history data from API
                start_time = time()
                history_end_date = to_datetime(history_end_date_ms).strftime('%d %b, %Y UTC')
                klines = client.get_historical_klines(
                    symbol.upper(), interval_string, history_start_date, history_end_date, limit=1000)
                logging.info("[{} s] {} history data missing for {} fetched".format(int((time() - start_time)), len(klines), stream_type))

                # formatting and inserting to DB
                try:

                    start_time = time()

                    requests = []
                    for entry in klines:
                        
                        record = {}
                        record['stream_type'] =         stream_type
                        record['start_time'] =          entry[0]
                        record['close_time'] =          entry[6]
                        record['open_price'] =          entry[1]
                        record['close_price'] =         entry[4]
                        record['high_price'] =          entry[2]
                        record['low_price'] =           entry[3]
                        record['number_of_trades'] =    entry[8]

                        requests.append(pymongo.ReplaceOne(
                            {"stream_type": record.get('stream_type'),
                            "close_time": record.get('close_time')},
                            record, upsert=True))

                    result = db.data.bulk_write(requests)

                    logging.info("[{} ms] [Missing records: {}] [Updated records: {}]".format(
                        int((time() - start_time) * 1000), result.upserted_count, result.modified_count))

                except Exception as e:
                    logging.error(e)

            else:

                logging.info("History for {} is already complete".format(stream_type))
         
        logging.info("Running history check again in 60 minutes")
        sleep(int(config['HISTORY_RUN_EVERY_MIN']) * 60)
