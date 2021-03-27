#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------
# Save Binance Websocket to local DB                                                 -
# https://pypi.org/project/unicorn-binance-websocket-api/                            -
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md -
# ------------------------------------------------------------------------------------

# Imports
import logging, requests, pymongo, config, mongodb
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
from time import sleep, time
from logging.config import fileConfig

def load_symbols():
    ''' load symbols from db that are marked for trading and return a list '''

    while(True):

        symbols = db.binance.symbols.find(
            filter={"tradeable": 1},
            projection={"_id": 0, "symbol": 1}
        )

        symbols = list(s['symbol'] for s in symbols)

        if len(symbols) > 0:
            logging.info(f"{len(symbols)} symbols found in the DB")
            return symbols

        logging.warning("No symbols marked for trading found in the DB. Retrying in 1 minute")

        sleep(60)

# call main function
if __name__ == "__main__":

    # set up logging
    fileConfig(config.env.LOGGING_CONFIG_FILE)

    # connect to the db
    mongodb = mongodb.Mongodb()
    db = mongodb.connect(config.env.DB_URI)

    # initialize DB
    logging.info("Creating collections/indexes for collection 'data' if not already present")
    db.binance.data.create_index([("stream_type", 1), ("close_time", -1)])

    # connecto to the Binance Websocket
    binance_websocket_api_manager = BinanceWebSocketApiManager(exchange=config.env.STREAM_EXCHANGE_URL)

    reload_symbols_time = time() + config.env.STREAM_RELOAD_SYMBOLS_EVERY_M * 60
    while True:

        # make a connection to the binance api websocket and get stream data for 1m candles and the coins that are market for trading
        symbols = load_symbols()
        
        # create stream
        stream_id = binance_websocket_api_manager.create_stream(["kline_1m"], symbols, output="UnicornFy")

        buffer = []
        while True:

            # stop/reload stream if the defined timeperiod has elapsed
            if time() > reload_symbols_time:
                logging.info("Stop stream")
                reload_symbols_time = time() + config.env.STREAM_RELOAD_SYMBOLS_EVERY_M * 60
                binance_websocket_api_manager.stop_stream(stream_id)
                break

            # read stream
            msg = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()

            if not msg:

                try:

                    if len(buffer) > 0:

                        # calculate execution time
                        start_time = time()

                        requests = []
                        for record in buffer:
                            requests.append(pymongo.ReplaceOne(
                                {"stream_type": record.get('stream_type'),
                                "close_time": record.get('close_time')},
                                record, upsert=True))

                        result = db.binance.data.bulk_write(requests)
                        logging.info("Stream processed in {} ms for {} active symbols ({} new documents inserted, {} documents updated)".format(
                            int((time() - start_time) * 1000), len(symbols), result.upserted_count, result.modified_count))
                            
                        buffer.clear()

                    else:
                        logging.info("The buffer is empty")

                except Exception as e:
                    logging.error(e)

                # wait
                sleep(int(config.env.STREAM_UPDATE_INTERVAL_S))

            else:
                try:

                    if msg.get('event_time'):

                        record = {}
                        kline = msg.get('kline')
                        record['stream_type'] =         msg.get('stream_type')
                        record['start_time'] =          kline.get('kline_start_time')
                        record['close_time'] =          kline.get('kline_close_time')
                        record['open_price'] =          kline.get('open_price')
                        record['close_price'] =         kline.get('close_price')
                        record['high_price'] =          kline.get('high_price')
                        record['low_price'] =           kline.get('low_price')
                        record['number_of_trades'] =    kline.get('number_of_trades')
                        record['is_closed'] =           kline.get('is_closed')

                        buffer.append(record)                      

                except Exception as e:
                    logging.error(e)
 
