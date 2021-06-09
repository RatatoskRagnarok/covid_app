#!/usr/bin/env python3

import json
from datetime import date

import geopandas as gpd
import pandas as pd
import streamlit as st


from get_data_functions import get_uk_data, uk_dict
from df_functions import prep_uk_df, rename_columns, add_pop_to_df

# setting page to wide
st.set_page_config(layout="wide")
# to make tooltips work in full screen graphs
st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
            unsafe_allow_html=True)

# title block
st.title('Squirrel Covid-19 😷 Data System')
st.write('By Ratatosk 🐿️')
st.write('v.3.0')

# list of data sources
with st.beta_expander('See my data sources...'):
    st.write('UK data comes from the UK government and can be downloaded [here]('
             'https://coronavirus.data.gov.uk/details/download)')
    st.write('World data comes from [Our World in Data](https://ourworldindata.org/). Their github repository is ['
             'here](https://github.com/owid/covid-19-data/tree/master/public/data)')
    st.write('US data comes from [Covid ActNow](https://covidactnow.org/?s=1859777) through their API, details of '
             'which are [here](https://apidocs.covidactnow.org/).')

# getting update date
try:
    with open('updates.json') as f:
        updates = json.load(f)
        update = updates['update']
except FileNotFoundError:
    update = None


@st.cache
def squirrelling_data(update):
    # uk dfs
    uk = prep_uk_df(uk_dict['uk'])
    nat = prep_uk_df(uk_dict['nation'])
    reg = prep_uk_df(uk_dict['region'])
    utlas = prep_uk_df(uk_dict['utla'])
    ltlas = prep_uk_df(uk_dict['ltla'])
    las = pd.concat([utlas, ltlas])
    las = las.reset_index().drop_duplicates(subset=['date', 'areaCode', 'newCases'], keep='first').set_index('date')
    # TODO msoa

    # uk places lists
    uk_places = ['UK'] + list(nat.areaName.unique()) + list(reg.areaName.unique())
    la_places = list(las.areaName.unique())
    # TODO msoa places


    # saving update date
    update = date.today()
    updates = {'update': update}
    with open('updates.json', 'w') as f:
        json.dump(updates, f, default=str)

    return uk, nat, reg, utlas, ltlas, las, uk_places, la_places


with st.spinner('Getting your data....'):
    uk, nat, reg, utlas, ltlas, las, uk_places, la_places = squirrelling_data(update)
    st.success('Done!')


st.dataframe(nat)
st.write(nat.columns)
