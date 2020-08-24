#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 09:23:31 2020

@author: Arjan Vermeulen

Implementation of trading algorithm
First, the bot checks if any positions are open.
Then, at 23:55, the bot will attempt to execute trades
"""

import binance
from binance.client import Client
from auth import key, secret
from datetime import datetime, timedelta
from time import sleep
from symbols import symbols, minTradeSizes
from notify_run import Notify

LEVERAGE = 3
PORTFOLIO_SPLIT = 0.1

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

# Check if all pairs were loaded
for symbol in symbols:
    assert symbol in positionDict.keys()

currentTime = datetime.today()
if currentTime.hour >= 12:
    tradeTime = currentTime + timedelta(days=1)
    tradeTime = tradeTime.replace(hour=12, minute=0, second=0, millisecond=0)
else:
    tradeTime = currentTime.replace(hour=12, minute=0, second=0, millisecond=0)

while True:
    if datetime.now() < tradeTime:
        sleep(60)
    else:
        tradeTime = tradeTime + timedelta(days=1)
        ## Trading Logic ##
        # The trading logic returns two lists:
        # One with the symbols to be longed,
        # One with the symbols to be shorted.
        tickers = client.get_ticker()
        priceDict = {}
        for tradingPair in tickers:
            for symbol in symbols:
                if tradingPair['symbol'] == f"{symbol}USDT":
                    priceDict[symbol] = float(tradingPair['lastPrice'])
                    
            
        long = []
        short = []
        
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
                newPosition = allocationUSDT / priceDict[symbol] 
                newPosition = newPosition - (newPosition % minTradeSizes[symbol])
                tradeDict[symbol] = newPosition - positionDict[symbol]
            elif symbol in short:
                newPosition = -1 * allocationUSDT / priceDict[symbol]
                newPosition = newPosition - (newPosition % minTradeSizes[symbol])
                tradeDict[symbol] = newPosition - positionDict[symbol]
            else:
                tradeDict[symbol] = -1 * positionDict[symbol]
                
        for symbol in symbols:
            if tradeDict[symbol] == 0:
                # Do not trade
                continue
            elif tradeDict[symbol] > 0:
                # Go long
                quantity = tradeDict[symbol]
                client.futures_create_order(symbol=f"{symbol}USDT",
                                            side=client.SIDE_BUY,
                                            type=client.ORDER_TYPE_MARKET,
                                            quantity=quantity
                                            )
            elif tradeDict[symbol] < 0:
                # Go short
                quantity = -1 * tradeDict[symbol]
                client.futures_create_order(symbol=f"{symbol}USDT",
                                            side=client.SIDE_SELL,
                                            type=client.ORDER_TYPE_MARKET,
                                            quantity=quantity)
        
        responseString = f"Balance: {balanceUSDT}"
        responseString = f"{responseString}\nLong:"
        for item in long:
            responseString = f"{responseString} item"
        responseString = f"{responseString}\nShort:"
        for item in short:
            responseString = f"{responseString} item"
        
        notify.send(responseString)
        print(responseString)
