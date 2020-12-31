# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 14:03:24 2020

@author: Arjan
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm

pd.set_option("display.max_rows", 10, "display.max_columns", None)

INDEX_SIZE = 10
INVESTABLE = 100

coins = pd.read_csv('data/all_data.csv')
mcapDate = coins.groupby('date_string')['market_cap'].agg(total_mcap = 'sum')
coinsMcap = coins.join(mcapDate, on='date_string', how='inner')
coinsMcapRank = (coinsMcap
                 .groupby('date_string')['market_cap']
                 .rank(ascending=False)
                 .to_frame()
                 )
coinsMcapRank.columns = ['rank']

coinsMcap = coinsMcap.join(coinsMcapRank)

crypto_index = 1/1_000_000 * (coinsMcap[coinsMcap['rank'] <= INDEX_SIZE]
                              .groupby('date_string')['market_cap']
                              .agg('sum')
                              )
bitcoin_index = 1/1_000_000 * (coinsMcap[coinsMcap['id'] == 'bitcoin']
                               .groupby('date_string')['market_cap']
                               .agg('sum')
                               )
# Drop days with missing BTC data
crypto_index = crypto_index[crypto_index.index.isin(bitcoin_index.index)]
index_returns = crypto_index.pct_change().fillna(0)
crypto_index = crypto_index.to_frame()
crypto_index.columns = ['crypto_index']
crypto_index.index.names = ['date_string']
index_returns = index_returns.to_frame()
index_returns.columns = ['return_index']
index_returns.index.names = ['date_string']

coinsReturns1d = (coinsMcap
                  .groupby('id')['price_usd']
                  .pct_change()
                  .fillna(0)
                  .to_frame()
                  )
coinsReturns1d.columns = ['return_1d']
coinsReturns7d = (coinsMcap
                  .groupby('id')['price_usd']
                  .pct_change(periods=7)
                  .fillna(0)
                  .to_frame()
                  )
coinsReturns7d.columns = ['return_7d']
coinsReturns30d = (coinsMcap
                   .groupby('id')['price_usd']
                   .pct_change(periods=30)
                   .fillna(0)
                   .to_frame()
                   )
coinsReturns30d.columns = ['return_30d']

coinsReturns = (coinsReturns1d
                .join(coinsReturns7d, how='outer')
                .join(coinsReturns30d, how='outer')
                )

invest = coinsMcap['rank'] <= INVESTABLE
invest = invest.to_frame()
invest.columns = ['investable']

coinsData = (coinsMcap
             .drop(['Unnamed: 0', 'Unnamed: 0.1'], axis=1)
             .join(invest, how='inner')
             .join(coinsReturns, how='inner')
             .join(crypto_index, on='date_string', how='inner')
             .join(index_returns, on='date_string', how='inner')
             )

coinsData.to_csv('data/processed_data.csv', header=True)

plt.plot(crypto_index)
plt.yscale('log')
plt.xlim('2014-01-01', '2020-12-31')
plt.ylim(1_000, 1_000_000)
plt.gca().axes.set_xticks([f"{year}-01-01" for year in range(2014, 2021)])
plt.grid(which='both', axis='both')
plt.xlabel('Date')
plt.ylabel('Score')
plt.title('Crypto index')
plt.show()