#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------
# Save Binance Websocket to local DB                                                 -
# https://pypi.org/project/unicorn-binance-websocket-api/                            -
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md -
# ------------------------------------------------------------------------------------

# Imports
import os
import logging
import pymongo
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
from time import sleep, time

# Functions
def load_config():
    ''' the configuration is loaded from the ENV variables.
        If they are not defined the default value specified here will be loaded '''

    global config
    config = {}

    logging.info("########## CONFIG ###########")
    set_variable('DB_URI', 'mongodb://crypto:Cr7ptopa55@localhost:27017')
    set_variable('EXCHANGE', 'binance.com')
    set_variable('UPDATE_INTERVAL_MS', 10000)
    set_variable('MARKETS', 'btcusdt, ethusdt, adausdt, linkusdt, ltcusdt')
    set_variable('CHANNELS', 'kline_1m')
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

def initialize_db():
    ''' create collections/indexes if not already present '''

    logging.info("Creating collections/indexes if not already present")
    db.data.create_index([("stream_type", 1), ("close_time", -1)])
    # db.symbols.create_index()

def update_symbols():
    logging.info("Updating Symbols")
    # TODO

# call main function
if __name__ == "__main__":

    # set up logging
    logging.basicConfig(format="%(asctime)s | %(levelname)s | %(module)s |  %(message)s",
                        level=os.getenv('LOG_LEVEL', 'INFO'),
                        datefmt="%Y-%m-%d %H:%M:%S")

    load_config()
    connect_db()
    initialize_db()
    update_symbols()

    markets = config['MARKETS'].split(', ')
    channels = config['CHANNELS'].split(', ')

    binance_websocket_api_manager = BinanceWebSocketApiManager(exchange=config['EXCHANGE'])
    binance_websocket_api_manager.create_stream(channels, markets, output="UnicornFy")

    buffer = []
    while True:

        msg = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()

        if not msg:

            try:

                if len(buffer) > 0:
                    logging.info("Processing {} records from the buffer".format(len(buffer)))

                    # calculate execution time
                    start_time = time()

                    requests = []
                    for record in buffer:
                        requests.append(pymongo.ReplaceOne(
                            {"stream_type": record.get('stream_type'),
                            "close_time": record.get('close_time')},
                            record, upsert=True))

                    result = db.data.bulk_write(requests)
                    logging.info("[{} ms] [Inserted: {}] [Updated: {}]".format(
                        int((time() - start_time) * 1000), result.upserted_count, result.modified_count))

                    buffer.clear()

                else:
                    logging.info("The buffer is empty")

            except Exception as e:
                logging.error(e)

            # wait
            sleep(int(config['UPDATE_INTERVAL_MS']) / 1000)

        else:
            try:

                if msg.get('event_time'):

                    record = {}
                    kline = msg.get('kline')
                    record['stream_type'] = msg.get('stream_type')
                    record['start_time'] =               kline.get('kline_start_time')
                    record['close_time'] =               kline.get('kline_close_time')
                    record['open_price'] =          kline.get('open_price')
                    record['close_price'] =         kline.get('close_price')
                    record['high_price'] =          kline.get('high_price')
                    record['low_price'] =           kline.get('low_price')
                    record['number_of_trades'] =    kline.get('number_of_trades')

                    buffer.append(record)                      

            except Exception as e:
                logging.error(e)
 
