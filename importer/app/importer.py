#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------
# Import data from CoinGecko API to the local DB                                -
# https://www.coingecko.com/api/documentations/v3                               -
# https://github.com/man-c/pycoingecko                                          -
# -------------------------------------------------------------------------------

# Imports
import os
import time
from pycoingecko import CoinGeckoAPI
from datetime import datetime
from pymongo import MongoClient
from multiprocessing import Process

# Functions
def load_config():
    global config
    config = {}

    print("#####################")
    print("Loading config")
    set_variable('DB_URI', 'mongodb://crypto:Cr7ptopa55@localhost:27017')
    set_variable('SCRAPE_INTERVAL', 10)
    set_variable('CURRENCY', 'USD')
    set_variable('LIMIT_COINS', 500)
    print("#####################")

def set_variable(key, default):
    global config
    config[key] = os.getenv(key, default)
    print("{}: {}".format(key, config[key]))

def connect_db():
    global db

    while(True):
        print("Connecting to DB...")

        try:
            client = MongoClient(config['DB_URI'])
            db = client.data
            status = db.command("serverStatus")
            print("Running MongoDB version {}".format(status.get('version')))
            break
        except Exception as error:
            print(error)

def connect_api():
    global cg
    print("Connecting to CoinGecko API...")
    cg = CoinGeckoAPI()

def get_top_coins():

    # Update the 500 coins with the biggets market capitalization
    print("Getting first {} coins with the biggest market capitalisation...".format(config['LIMIT_COINS']))

    # delete first coins collection to avoid duplicates
    db.coins.delete_many({})

    pages = int(int(config['LIMIT_COINS']) / 100)
    
    for x in range(1, pages+1):
        print("Getting page {} of {}".format(x, pages))
        coins = cg.get_coins_markets(config['CURRENCY'], page=x)
        db.coins.insert_many(coins)

    # Create index
    db.coins.create_index([("market_cap", -1)])

    print("Finished updating coins table...")

def load_coin_list():
    
    # Get coin list list
    result = db.coins.find(
        filter={},
        projection={'id': 1, '_id': 0},
        sort=[('market_cap', -1)],
        limit=100
    )
    coin_list = [d['id'] for d in list(result)]
    print("Coin list loaded: {}".format(coin_list))
    return coin_list

def get_actual_price(coin_list):

    while(True):
        print("Getting actual price for {} coins...".format(len(coin_list)))

        response = cg.get_price(
            ids=coin_list,
            vs_currencies=config['CURRENCY'],
            include_market_cap='true',
            include_24hr_vol='true'
        )

        prices = []
        for id in response:
            data = response[id]
            currency = config['CURRENCY'].lower()
            price = {}
            price['time'] = int(time.time())
            price['id'] = id
            price['currency'] = config['CURRENCY'].lower()
            price['market_cap'] = data.get("{}_market_cap".format(currency))
            price['volume'] = data.get("{}_24h_vol".format(currency))
            prices.append(price)

        db.price.insert_many(prices)

        print("Price for {} coins updated".format(len(prices)))

        time.sleep(int(config['SCRAPE_INTERVAL']))

# Call main function
if __name__ == "__main__":

    load_config()
    connect_db()
    connect_api()
    get_top_coins()
    get_actual_price(load_coin_list())