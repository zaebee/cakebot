"""Gets cake orders from gsheet file or from csv.
"""

import os
import datetime as dt

from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()

SHEET_ID = os.getenv('SHEET_ID')
G_IDS = ['959471842', '299460191']

EXPORT_URL = 'https://docs.google.com/spreadsheets/d/{id}/export?gid={gid}&format=csv'


def _cakes_df(url):
    df = pd.read_csv(url, index_col=0).reset_index()
    df = df.rename(str.lower, axis='columns')
    df = df.rename(str.strip, axis='columns')
    df = df.rename(columns={
        'дата': 'date',
        #'торт': 'cake',
        'десерты (торт)': 'cake',
        #'билеты': 'cake',
        'время': 'time',
        'заказчик': 'client',
        'телефон': 'phone',
        'место': 'room',
        'комната': 'room',
        'кол-во гостей': 'persons',
        'меню': 'comment',
        'коммент': 'comment',
        'Стоимость': 'price',
        'Аниматор + программа': 'program',
        'Бронь (встреча) ': 'meet_notes',
    })

    df = df[~df.cake.isna()]
    df.date = pd.to_datetime(df.date, format='%d.%m.%Y')
    df.time = df.time.map(lambda x: str(x).replace('.', ':'))
    df['day'] = df.date.dt.strftime('%d.%m')
    return df


def _clean_df(df, filter_words=''):
    filters = df.cake.str.match('-')
    filters |= df.cake.str.match('нет')
    for word in filter_words:
        filters |= df.cake.str.contains(word, case=False)
    return df[~filters]


def actual_orders():
    """Returns list of actual cake order."""
    dfs = []
    filter_words = ['сбор', 'думают', 'думает']
    for gid in G_IDS:
        url = EXPORT_URL.format(id=SHEET_ID, gid=gid)
        df = _clean_df(_cakes_df(url), filter_words)
        dfs.append(
            df[df.date >= np.datetime64(dt.date.today())][['date', 'day', 'time', 'cake']]
        )

    df = pd.concat(dfs)
    df = df.reset_index().drop_duplicates(subset=['date', 'time'])
    return df[['day', 'time', 'cake']]#.set_index(['day_of_month', 'time'])