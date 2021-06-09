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

df = prep_uk_df(uk_dict['uk'])
st.dataframe(df)
st.write(df.columns)
