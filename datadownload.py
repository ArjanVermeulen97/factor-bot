#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 17:16:31 2020

@author: Arjan Vermeulen

This program downloads past daily data from Binance
and saves it to csv files for processing.

The data is recorded on a daily timeframe, with the following factors:
    daily return: close/open
    daily range to price: (high - low)/open
    1/7/30 day momentum: close/open
    daily volume
    market cap
    reddit posts/comments
    alexa rank
"""

import binance                            # Needed for exception handling
from binance.client import Client         # Binance API Client
from auth import key, secret              # Binance API key
import pandas as pd                       # Data processing
from pycoingecko import CoinGeckoAPI      # Coingecko for mcap, social data
from datetime import datetime, timedelta  # Needed for API rate limit
from time import sleep                    # Needed for API rate limit
import threading                          # threaded write

# Start and end date
START_DATE = "07-18-2019"
END_DATE = "07-31-2020"

# All symbols available on Binance futures as per 23-AUG-2020
symbols = ["BTC", "ETH", "LINK", "OMG", "DOT",
           "ATOM", "SXP", "BAND", "KAVA", "XTZ",
           "ZRX", "LTC", "EOS", "WAVES", "BCH",
           "XRP", "NEO", "ALGO", "BAT", "TRX",
           "ADA", "LEND", "THETA", "RLC", "ONT",
           "COMP", "QTUM", "BNB", "ETC", "ZEC",
           "VET", "IOST", "MKR", "SNX", "XLM",
           "KNC", "XMR", "IOTA", "ZIL", "DASH",
           "DOGE"]

client = Client(key, secret)
cg = CoinGeckoAPI()
coinsList = cg.get_coins_list()

def get_cg_data(symbol, date):
    cgId = cgSymbols[symbol]
    history = cg.get_coin_history_by_id(id=cgId,
                                        date=date,
                                        localization=False)
    try:
        marketCap = history['market_data']['market_cap']['usd']
    except KeyError:
        marketCap = None
    try:
        alexaRank =  history['public_interest_stats']['alexa_rank']
    except KeyError:
        alexaRank = None
    try:
        redditPosts =  history['community_data']['reddit_average_posts_48h']
    except KeyError:
        redditPosts = None
    try:
        redditComments = history['community_data']['reddit_average_comments_48h']
    except KeyError:
        redditComments = None

    response = {'market_cap': marketCap,
                'alexa_rank': alexaRank,
                'reddit_posts': redditPosts,
                'reddit_comments': redditComments}
    
    return response


def get_binance_data(symbol, date):
    OHLCVData = client.get_historical_klines(f"{symbol}USDT",
                                                 Client.KLINE_INTERVAL_1DAY,
                                                 date,
                                                 date)
    try:
        openPrice = float(OHLCVData[0][1])
    except IndexError:
        openPrice = None
    try:
        highPrice = float(OHLCVData[0][2])
    except IndexError:
        highPrice = None
    try:
        lowPrice = float(OHLCVData[0][3])
    except IndexError:
        lowPrice = None
    try:
        closePrice = float(OHLCVData[0][4])
    except IndexError:
        closePrice = None
    try:
        volume = float(OHLCVData[0][5])*openPrice
    except (IndexError, TypeError):
        volume = None
        
    response = {'open': openPrice,
                'high': highPrice,
                'low': lowPrice,
                'close': closePrice,
                'volume': volume}
    
    return response


def pd_write(dataframe, date):
    dataframe.to_csv(f"./datafiles/data_{date}", index=False)
    return 0


# Corresponding CoinGecko ID's
cgSymbols = {}
for coin in coinsList:
    if coin['symbol'].upper() in symbols:
        cgSymbols[coin['symbol'].upper()] = coin['id']
    elif coin['id'].upper() in symbols:
        cgSymbols[coin['id'].upper()] = coin['id']
        
# Data to be gathered
dataColumns = ["asset", "date", "return_1d", "range_to_price", "momentum_1d",
               "momentum_7d", "momentum_30d", "volume_1d", "market_cap",
               "alexa_rank", "reddit_posts_48h", "reddit_comments_48h"]

dates = pd.date_range(START_DATE, END_DATE).to_list()
startTime = datetime.now()

for date in dates:
    print(date.strftime('%d-%m-%Y'))
    data = pd.DataFrame(columns=dataColumns)
    for coin in symbols:
        # Comply with CoinGecko API rate limit
        while datetime.now() - startTime < timedelta(seconds=1):
            sleep(0.01)
        startTime = datetime.now()
        
        # Fetch data
        binanceDate = date.strftime('%m-%d-%Y')
        binanceDateWeekAgo = (date - timedelta(days=7)).strftime('%m-%d-%Y')
        binanceDateMonthAgo = (date - timedelta(days=30)).strftime('%m-%d-%Y')
        coingeckoDate = date.strftime('%d-%m-%Y')
        
        binanceData = get_binance_data(coin, binanceDate)
        openWeekAgo = get_binance_data(coin, binanceDateWeekAgo)['open']
        openMonthAgo = get_binance_data(coin, binanceDateMonthAgo)['open']
        CGData = get_cg_data(coin, coingeckoDate)
        
        # Process data
        try:
            return_1d = binanceData['close'] / binanceData['open']
        except TypeError:
            return_1d = None
        try:
            range_to_price = (binanceData['high'] - binanceData['low']) / binanceData['open']
        except TypeError:
            range_to_price = None
        try:
            momentum_1d = binanceData['close'] / binanceData['open'] - 1
        except TypeError:
            momentum_1d = None
        try:
            momentum_7d = binanceData['close'] / openWeekAgo - 1
        except TypeError:
            momentum_7d = None
        try:
            momentum_30d = binanceData['close'] / openMonthAgo - 1
        except TypeError:
            momentum_30d = None
        try:
            volume_1d = binanceData['volume']
        except TypeError:
            volume_1d = None
        try:
            market_cap = CGData['market_cap']
        except TypeError:
            market_cap = None
        try:
            alexa_rank = CGData['alexa_rank']
        except TypeError:
            alexa_rank = None
        try:
            reddit_posts = CGData['reddit_posts']
        except TypeError:
            reddit_posts = None
        try:
            reddit_comments = CGData['reddit_comments']
        except TypeError:
            reddit_comments = None
        
        entry = {'asset': coin,
                 'date': date,
                 'return_1d': return_1d,
                 'range_to_price': range_to_price,
                 'momentum_1d': momentum_1d,
                 'momentum_7d': momentum_7d,
                 'momentum_30d': momentum_30d,
                 'volume_1d': volume_1d,
                 'market_cap': market_cap,
                 'alexa_rank': alexa_rank,
                 'reddit_posts_48h': reddit_posts,
                 'reddit_comments_48h': reddit_comments}
        
        data = data.append(entry, ignore_index=True)
    
    writer = threading.Thread(group=None,
                              target=pd_write,
                              name="Thread-writer",
                              args=(data, coingeckoDate)
                              )
    writer.run()
        
        
        