#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 09:23:31 2020

@author: Arjan Vermeulen

Implementation of trading algorithm
First, the bot checks if any positions are open.
Then, at 12:00, the bot will attempt to execute trades
"""

import binance
from binance.client import Client
from auth import key, secret
from datetime import datetime, timedelta
from time import sleep
from symbols import symbols, minTradeSizes
from notify_run import Notify
import pandas as pd
import os

LEVERAGE = 2
PORTFOLIO_SPLIT = 5

client = Client(key, secret)
notify = Notify()

def get_position():
    '''This function returns the account balance in USDT, as well as
    a dictionary of all position in different assets.'''
    position = client.futures_position_information()
    balanceUSDT = float(client.futures_account_balance()[0]['balance'])
    positionDict = {}
    
    for tradingPair in position:
        for symbol in symbols:
            if tradingPair['symbol'] == f"{symbol}USDT":
                positionAmt = float(tradingPair['positionAmt'])
                entryPrice = float(tradingPair['entryPrice'])
                liquidationPrice = float(tradingPair['liquidationPrice'])
                if positionAmt > 0:
                    if liquidationPrice < entryPrice:
                        # Long position
                        positionDict[symbol] = positionAmt
                    else:
                        # Short position
                        positionDict[symbol] = -1 * positionAmt
                else:
                    # No position
                    positionDict[symbol] = 0
                    
    return balanceUSDT, positionDict

balanceUSDT, positionDict = get_position()

# Check if all pairs were loaded, and set leverage.
for symbol in symbols:
    assert symbol in positionDict.keys()
    client.futures_change_leverage(symbol=f"{symbol}USDT",
                                   leverage=LEVERAGE+1)

currentTime = datetime.today()
if currentTime.hour >= 12:
    tradeTime = currentTime + timedelta(days=1)
    tradeTime = tradeTime.replace(hour=12, minute=0, second=0, microsecond=0)
else:
    tradeTime = currentTime.replace(hour=12, minute=0, second=0, microsecond=0)

tradeTime = datetime.now()

while True:
    if datetime.now() < tradeTime:
        sleep(60)
    else:
        # TO DO
        os.system("Do thing")
        tradeTime = tradeTime + timedelta(days=1)
        # First, we cancel all remaining orders.
        client.futures_cancel_all_open_orders()
        ## Trading Logic ##
        # The trading logic returns two lists:
        # One with the symbols to be longed,
        # One with the symbols to be shorted.
        priceDict = {}
        tradingData = pd.DataFrame(columns=["asset",
                                            "momentum_1d",
                                            "momentum_7d"])
        for symbol in symbols:
            priceData = client.get_historical_klines(f"{symbol}USDT",
                                                     client.KLINE_INTERVAL_1HOUR,
                                                     "169 hours ago")
            try:
                currentPrice = float(priceData[-1][4])
                open1Day = float(priceData[144][3])
                open1Week = float(priceData[0][3])
            except IndexError:
                continue
            priceDict[symbol] = currentPrice
            tradeData = {"asset": symbol,
                         "momentum_1d": currentPrice / open1Day - 1,
                         "momentum_7d": currentPrice / open1Week - 1}
            tradingData = tradingData.append(tradeData, ignore_index=True)
            
        tradingData['momentum_comb'] = tradingData['momentum_1d'] + tradingData['momentum_7d']
        tradingData['quantile'] = tradingData['momentum_comb'].rank(pct=True)
        tradingData['portfolio'] = pd.cut(tradingData['quantile'],
                                          bins=PORTFOLIO_SPLIT,
                                          labels=False)
        long = tradingData.loc[tradingData['portfolio'] == PORTFOLIO_SPLIT-1, 'asset']
        short = tradingData.loc[tradingData['portfolio'] == 0, 'asset']
        long = long.to_list()
        short = short.to_list()
        
        ## Execution ##
        # Calculate needed position sizes
        # And differences with current positions
        # Then execute trades
        balanceUSDT, positionDict = get_position()
        
        # Amount allocated to each position
        allocationUSDT = balanceUSDT * 0.95 / (len(long) + len(short))
        
        # Calculate amounts to be traded
        tradeDict = {}
        for symbol in symbols:
            if symbol in long:
                newPosition = LEVERAGE * allocationUSDT / priceDict[symbol] 
                newPosition = newPosition - (newPosition % minTradeSizes[symbol])
                tradeDict[symbol] = newPosition - positionDict[symbol]
            elif symbol in short:
                newPosition = -1 * LEVERAGE * allocationUSDT / priceDict[symbol]
                newPosition = newPosition - (newPosition % minTradeSizes[symbol])
                tradeDict[symbol] = newPosition - positionDict[symbol]
            else:
                tradeDict[symbol] = -1 * positionDict[symbol]
                
        for symbol in symbols:
            if tradeDict[symbol] == 0:
                continue
            elif tradeDict[symbol] > 0:
                quantity = tradeDict[symbol]
                client.futures_create_order(symbol=f"{symbol}USDT",
                                            side=client.SIDE_BUY,
                                            type=client.ORDER_TYPE_LIMIT,
                                            timeInForce=client.TIME_IN_FORCE_GTC,
                                            price=str(priceDict[symbol]),
                                            quantity=f"{quantity:.3}"
                                            )
                sleep(0.1) # Comply with API rate limit
            elif tradeDict[symbol] < 0:
                quantity = -1 * tradeDict[symbol]
                client.futures_create_order(symbol=f"{symbol}USDT",
                                            side=client.SIDE_SELL,
                                            type=client.ORDER_TYPE_LIMIT,
                                            timeInForce=client.TIME_IN_FORCE_GTC,
                                            price=str(priceDict[symbol]),
                                            quantity=f"{quantity:.3}"
                                            )
                sleep(0.1) # Comply with API rate limit
                
        
        responseString = f"Balance: {balanceUSDT:.5}"
        responseString = f"{responseString}\nLong:"
        for item in long:
            responseString = f"{responseString} {item}"
        responseString = f"{responseString}\nShort:"
        for item in short:
            responseString = f"{responseString} {item}"
        
        notify.send(responseString)
        print(responseString)
