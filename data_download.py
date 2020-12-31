# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 21:42:12 2020

@author: Arjan
"""

from pycoingecko import CoinGeckoAPI
from datetime import datetime
import time
import pandas as pd

cg = CoinGeckoAPI()

coinsList = cg.get_coins_list()
coins = pd.DataFrame(columns=['date_unix',
                              'date_string',
                              'id',
                              'symbol',
                              'name',
                              'price_usd',
                              'market_cap',
                              'volume']
                     )

for index, symbol in enumerate(coinsList):
    print(f"{index}/{len(coinsList)}: {symbol['name']}")
    try:
        coin = pd.read_csv(f"data/{symbol['id']}_data.csv")
        coins = coins.append(coin,
                            ignore_index=True,
                            )
        print(">>> Succesfully loaded data")
        continue
    except FileNotFoundError:
        this_coin = pd.DataFrame(columns=['date_unix',
                              'date_string',
                              'id',
                              'symbol',
                              'name',
                              'price_usd',
                              'market_cap',
                              'volume']
                                )
        coinData = None
        time.sleep(0.6)
        while coinData is None:
            try:
                coinData = cg.get_coin_market_chart_by_id(id=symbol['id'],
                                                          vs_currency='usd',
                                                          days=30000,
                                                          interval='daily'
                                                          )
            except Exception as e:
                print(e)
                time.sleep(10)
                print("Resuming...")
        
        n_days = len(coinData['prices'])
        if n_days < 31:
            coin = {'date_unix': 0,
                    'date_string': '1970-01-01',
                    'id': symbol['id'],
                    'symbol': symbol['symbol'],
                    'name': symbol['name'],
                    'price_usd': 0,
                    'market_cap': 0,
                    'volume': 0}
            
            coin = pd.DataFrame.from_records([coin])
            coin.to_csv(f"data/{symbol['id']}_data.csv")
            print(">>> Insufficient data")
            continue
        
        for day in range(n_days-1):
            date_unix = coinData['prices'][day][0]
            date_string = datetime.utcfromtimestamp(date_unix/1000).strftime('%Y-%m-%d')
            coin_id = symbol['id']
            coin_symbol = symbol['symbol']
            coin_name = symbol['name']
            coin_price = coinData['prices'][day][1]
            coin_mcap = coinData['market_caps'][day][1]
            coin_volume = coinData['total_volumes'][day][1]
            
            #Validation
            if type(date_unix) != int:
                continue
            if type(date_string) != str:
                continue
            if type(coin_id) != str:
                continue
            if type(coin_symbol) != str:
                continue
            if type(coin_name) != str:
                continue
            
            if type(coin_price) != float:
                continue
            elif coin_price <= 0:
                continue
            if type(coin_mcap) != float:
                continue
            elif coin_mcap <= 0:
                continue
            if type(coin_volume) != float:
                continue
            elif coin_volume <= 0:
                continue
            
            coin = {'date_unix': date_unix,
                    'date_string': date_string,
                    'id': coin_id,
                    'symbol': coin_symbol,
                    'name': coin_name,
                    'price_usd': coin_price,
                    'market_cap': coin_mcap,
                    'volume': coin_volume}
            
            coin = pd.DataFrame.from_records([coin])
            this_coin = this_coin.append(coin,
                                         ignore_index=True
                                         )
            
        this_coin.to_csv(f"data/{symbol['id']}_data.csv")
        coins = coins.append(this_coin,
                            ignore_index=True,
                            )
        print(f">>> Processed {n_days} days")

print("Complete! Writing to file...")
coins.drop(coins[coins.market_cap == 0].index, inplace=True)
coins.drop(coins[coins.market_cap > 10**12].index, inplace=True)
coins.to_csv('data/all_data.csv', header=True)
print("Done!")