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

# functions
def get_coin_details(symbol):
    ''' get coin details from list of coins '''

    symbol = symbol.replace(config.env.SYMBOLS_FILTER, "").lower()

    for coin in coinGekoCoins:
        if coin.get('symbol') == symbol:
            return coin

    return None

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

        filtered_symbols = []
        for symbol in symbols:
            if config.env.SYMBOLS_FILTER in symbol.get('symbol'):
                filtered_symbols.append(symbol.get('symbol'))

        logging.info(f'Found {len(filtered_symbols)} symbols with filter "{config.env.SYMBOLS_FILTER}" traded on Binance')
        
        # filter symbols
        coinGekoCoins = []
        for i in range (0,config.env.SYMBOLS_COINGEKO_PAGES): # every page has max 250 coins
            coinGekoCoins += cg.get_coins_markets('USD', page=i, per_page=250)

        logging.info("{} coins imported from CoinGeko".format(len(coinGekoCoins)))

        # get_coin_details("ETHUSDT")


        # formatting and inserting to DB
        try:

            start_time = time()

            bulkUpdate = []
            for symbol in filtered_symbols:

                coin = get_coin_details(symbol)

                if coin:
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
            
            skipped_symbols = len(filtered_symbols) - len(bulkUpdate)
            if skipped_symbols > 0:
                logging.info(f"Skipping {skipped_symbols} symbols because not found on CoinGeko and probably have very low marke cap")

            result = db.binance.symbols.bulk_write(bulkUpdate)
            logging.info("[{} ms] {} symbols updated successfully".format(int((time() - start_time) * 1000), result.matched_count))

        except Exception as e:
            logging.error(e)

        logging.info("Updating again in {} minutes".format(config.env.SYMBOLS_IMPORT_EVERY_M))
        sleep(int(config.env.SYMBOLS_IMPORT_EVERY_M) * 60)
