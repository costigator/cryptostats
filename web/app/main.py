import config
from pymongo import MongoClient
from fastapi import FastAPI, Form
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")
db = MongoClient(config.DB_URI)

@app.get("/")
def index(request: Request):

    symbols = db.binance.symbols.find(
        projection={"_id": 0},
        sort=[('market_cap', -1)]
    )

    # integrity
    integrity = {}
    data_integrity_list = db.binance.checkpoints.find(
        projection={"_id": 0, "stream_type": 1, "bars_percent_complete": 1},
        sort=[('market_cap', 1)]
    )
    for i in data_integrity_list:
        integrity[i.get('stream_type', 'error')] = i.get('bars_percent_complete', 0)

    # new closing highs
    nch = db.binance.stats.find(
        projection={"_id": 0},
    )
    nch = list(nch)

    results = []
    for s in symbols:

        # format
        try:
            s['market_cap'] = int(s.get('market_cap') / 1000000)
        except:
            s['market_cap'] = 0

        # volatility
        try:
            s['volatility_15m'] = s['volatility']['15m']
            s['volatility_1h'] = s['volatility']['1h']
        except:
            s['volatility_15m'] = 0
            s['volatility_1h'] = 0

        # 24h change color
        try:
            s['price_change_percentage_24h'] = round(s['price_change_percentage_24h'], 2)
            if s['price_change_percentage_24h'] > 0:
                s['price_change_percentage_24h_color'] = "green"
            elif s['price_change_percentage_24h'] < 0:
                s['price_change_percentage_24h_color'] = "red"
            else:
                s['price_change_percentage_24h_color'] = "grey"
        except:
            s['price_change_percentage_24h'] = 0
            s['price_change_percentage_24h_color'] = "grey"

        # integrity
        s['integrity_1m'] = integrity.get(f"{s['symbol'].lower()}@kline_1m", 0)
        if s['integrity_1m'] > 99.8:
            s['integrity_1m'] = 3
        elif s['integrity_1m'] > 95:
            s['integrity_1m'] = 2
        elif s['integrity_1m'] > 0:
            s['integrity_1m'] = 1

        # defaults
        s['new_closing_highs_24h'] = 0

        # new closing highs
        for i in nch:
            if i.get('symbol') == s.get('symbol'):
                s['new_closing_highs_24h'] = int(float(i.get("close")) * 100 / float(i.get("high")))
                # continue

        results.append(s)

    # print(results)

    return templates.TemplateResponse("index.html", {"request": request, "symbols": results})

@app.get("/symbol/{symbol}")
def symbol_detail(request: Request, symbol):
    stream_type = "{}@kline_1m".format(symbol.lower())
    bars = db.binance.data.find(
        filter={"stream_type": stream_type},
        projection={"_id": 0, "stream_type": 0, "start_time": 0},
        sort=[('close_time', -1)]
    ).limit(100)
    return templates.TemplateResponse("symbol.html", {"request": request, "symbol": symbol, "exchange": "binance", "bars": list(bars)})

@app.post("/activate/{symbol}")
def activate_symbol(request: Request, symbol):

    db.binance.symbols.update_one(
        {
            "symbol": symbol.upper()
        }, {
            "$set": {
                "tradeable": 1
            }
        }, 
        upsert=True
    )

    return RedirectResponse(url="/", status_code=303)

@app.post("/deactivate/{symbol}")
def deactivate_symbol(request: Request, symbol):

    db.binance.symbols.update_one(
        {
            "symbol": symbol.upper()
        }, {
            "$set": {
                "tradeable": 0
            }
        }, 
        upsert=True
    )

    return RedirectResponse(url="/", status_code=303)
