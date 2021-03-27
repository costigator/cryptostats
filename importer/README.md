# Importer

The importer has the following scripts:

- get_symbols.py: get all the symbols with the defined filter from Binance and get also some details from CoinGeko. Store the result in the symbols collection
- get_history.py: get the history for every symbol and channel (1m, 5m, ...) and store the result in the data collection
- get_stream.py: get real-time data for the trading symbols for the 1m channel. The result is also stored in the data collection

## CoinGeko API

Example of API response:

```json
{
    'ath': 58641,
    'ath_change_percentage': -3.26153,
    'ath_date': '2021-02-21T19:07:32.042Z',
    'atl': 67.81,
    'atl_change_percentage': 83558.77717,
    'atl_date': '2013-07-06T00:00:00.000Z',
    'circulating_supply': 18650887.0,
    'current_price': 56971,
    'fully_diluted_valuation': 1191683820269,
    'high_24h': 57369,
    'id': 'bitcoin',
    'image': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png?1547033579',
    'last_updated': '2021-03-11T13:58:14.542Z',
    'low_24h': 54564,
    'market_cap': 1058379060551,
    'market_cap_change_24h': 13822186661,
    'market_cap_change_percentage_24h': 1.32326,
    'market_cap_rank': 1,
    'max_supply': 21000000.0,
    'name': 'Bitcoin',
    'price_change_24h': 765.31,
    'price_change_percentage_24h': 1.36161,
    'roi': None,
    'symbol': 'btc',
    'total_supply': 21000000.0,
    'total_volume': 63829038188
}
```
