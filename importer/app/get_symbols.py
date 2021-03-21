#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------------------
# Get symbols and store them in the DB                                                  -
# ---------------------------------------------------------------------------------------

import config, mongodb, logging, requests
from pymongo import UpdateOne
from logging.config import fileConfig
from pycoingecko import CoinGeckoAPI
from time import sleep, time

# call main function
if __name__ == "__main__":

    # set up logging
    fileConfig(config.env.LOGGING_CONFIG_FILE)

    # connect to the db
    mdb = mongodb.Mongodb()
    db = mdb.connect(config.env.DB_URI)

    # initialize DB
    logging.info("Creating collections/indexes if not already present")
    db.binance.symbols.create_index([("symbol", 1)])
    db.binance.symbols.create_index([("market_cap", -1)])

    # connect to CoinGeko
    logging.info("Connecting to CoinGecko API")
    cg = CoinGeckoAPI()

    while(True):

        # get all symbols traded on binance
        url = '{}/exchangeInfo'.format(config.env.BINANCE_API_URL)
        result = requests.get(url).json()
        symbols = result.get('symbols')

        all_symbols = []
        for symbol in symbols:
            all_symbols.append(symbol.get('symbol'))

        logging.info("Found {} symbols traded on Binance".format(len(all_symbols)))
        
        # filter symbols
        coinGekoCoins = []
        for i in range (0,2): # get first 2 pages with each 250 coins
            coinGekoCoins += cg.get_coins_markets('USD', page=i, per_page=250)

        logging.info("{} coins imported from CoinGeko".format(len(coinGekoCoins)))

        # formatting and inserting to DB
        logging.info("Filtering symbols with USDT only")
        try:

            start_time = time()

            bulkUpdate = []
            for coin in coinGekoCoins:

                symbol = "{}{}".format(coin.get('symbol').upper(), 'USDT')

                if symbol in all_symbols:
                    record = {}
                    record['market_cap'] = coin.get('market_cap')
                    record['image'] = coin.get('image')
                    record['name'] = coin.get('name')
                    record['exchange'] = 'binance'
                    record['price_change_percentage_24h'] = coin.get('price_change_percentage_24h')
                    
                    bulkUpdate.append(UpdateOne(
                        {
                            "symbol": symbol
                        }, {
                            "$set": record
                        }, 
                        upsert=True)
                    )
                
            result = db.binance.symbols.bulk_write(bulkUpdate)

            logging.info("[{} ms] {} symbols updated successfully".format(int((time() - start_time) * 1000), result.matched_count))

        except Exception as e:
            logging.error(e)

        logging.info("Updating again in {} minutes".format(config.env.IMPORT_SYMBOLS_EVERY_M))
        sleep(int(config.env.IMPORT_SYMBOLS_EVERY_M) * 60)
