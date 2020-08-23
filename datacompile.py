#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 21:18:56 2020

@author: Arjan Vermeulen

Combines loose date files into one file
"""

import pandas as pd

START_DATE = "01-01-2017"
END_DATE = "31-07-2017"

dates = pd.date_range(START_DATE, END_DATE).to_list()
dataColumns = ["asset", "date", "return_1d", "range_to_price", "momentum_1d",
               "momentum_7d", "momentum_30d", "volume_1d", "market_cap",
               "alexa_rank", "reddit_posts_48h", "reddit_comments_48h"]
data = pd.DataFrame(columns=dataColumns)

for date in dates:
    dateString = date.strftime('%d-%m-%Y')
    file = pd.read_csv(f"./datafiles/data_{dateString}")
    data = data.append(file, ignore_index=True)

data.to_csv("data.csv", index=False)
        