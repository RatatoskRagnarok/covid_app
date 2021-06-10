#!/usr/bin/env python3

import json
from datetime import date

import geopandas as gpd
import pandas as pd
import streamlit as st

from get_data_functions import get_uk_data, uk_dict
from df_functions import prep_uk_df, rename_columns, add_pop_to_df, prep_msoa, prep_us_df, prep_world_df, make_summary

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


@st.cache
def squirrelling_uk_data(today):
    # uk dfs
    uk = prep_uk_df(uk_dict['uk'])
    nat = prep_uk_df(uk_dict['nation'])
    reg = prep_uk_df(uk_dict['region'])
    utlas = prep_uk_df(uk_dict['utla'])
    ltlas = prep_uk_df(uk_dict['ltla'])
    las = pd.concat([utlas, ltlas])
    las = las.reset_index().drop_duplicates(subset=['date', 'areaCode', 'newCases'], keep='first').set_index('date')
    # removing msoas, they take too long for too little value
    # msoa = prep_msoa()

    # uk places lists
    uk_places = ['UK'] + list(nat.areaName.unique()) + list(reg.areaName.unique())
    la_places = list(las.areaName.unique())
    # msoa_places = list(msoa.areaName2.unique())

    return uk, nat, reg, utlas, ltlas, las, uk_places, la_places


@st.cache
def squirrelling_us_data(today):
    us = prep_us_df(us=True)
    states = prep_us_df(state=True)
    counts = prep_us_df(county=True)

    us_places = ['US'] + list(states.areaName.unique())
    county_places = list(counts.areaName.unique())

    return us, states, counts, us_places, county_places


@st.cache
def squirrelling_the_world(today):
    world = prep_world_df()
    world_places = list(world.areaName.unique())
    return world, world_places


def uk_choice_form(key):
    with st.form(key=key):
        st.write('Choose one of the following options:')
        st.text('If you select one of each option, it will only use the first one!')
        uk_choice1 = st.selectbox('Choose the whole UK, a nation or region:', [None]+uk_places, key=key)
        st.write('OR')
        uk_choice2 = st.selectbox('Choose a UK local authority:', [None]+la_places, key=key)
        submitted = st.form_submit_button('Go!')

    if submitted:
        if uk_choice1 and uk_choice2:
            st.error('One of the values needs to be None!')
        if uk_choice1:
            if uk_choice1 == 'UK':
                return uk
            if uk_choice1 in nat.areaName.unique():
                return nat[nat.areaName == uk_choice1]
            else:
                return reg[reg.areaName == uk_choice1]
        if uk_choice2 and not uk_choice1:
            return las[las.areaName == uk_choice2]


def us_choice_form(key):
    with st.form(key=key):
        st.write('Choose one of the following options:')
        st.text('If you select one of each option, it will only use the first one!')
        us_choice1 = st.selectbox('Choose the whole US or a state:', [None]+us_places, key=key)
        st.write('OR')
        us_choice2 = st.selectbox('Choose a US county:', [None]+county_places, key=key)
        submitted = st.form_submit_button('Go!')

        if submitted:
            if us_choice1 and us_choice2:
                st.error('One of the values needs to be None!')
            if us_choice1:
                if us_choice1 == 'US':
                    return us
                else:
                    return states[states.areaName == us_choice1]
            if us_choice2 and not us_choice1:
                return counts[counts.areaName == us_choice2]


def world_choice_form(key):
    with st.form(key=key):
        st.write('Choose somewhere in the world!')
        world_choice = st.selectbox('Choose a place in the world:', world_places, key=key)
        submitted = st.form_submit_button('Go!')

        if submitted:
            return world[world.areaName == world_choice]


with st.spinner('Getting UK data....'):
    uk, nat, reg, utlas, ltlas, las, uk_places, la_places = squirrelling_uk_data(date.today())

with st.spinner('Getting US data.... This can take a while....'):
    us, states, counts, us_places, county_places = squirrelling_us_data(date.today())

with st.spinner('Getting world data...'):
    world, world_places = squirrelling_the_world(date.today())

# Summary
with st.beta_container():
    st.header('Summaries')
    st.text('Please note not all data is available for all areas and some places do not update data daily')
    with st.beta_expander('Information on missing UK R rate data: '):
        st.text('The UK government stopped giving transmission rate (R) data for the whole UK in March 2021')
        st.text('Transmission rate (R) is available for individual nations in the UK')
        st.text('Or go to "World" and look at their UK entry.')
    choose = st.selectbox('Choose a place to show a summary for:', ['Somewhere in the UK',
                                                                    'Somewhere in the US',
                                                                    'Somewhere in the World'], key='summary')
    place_df = uk
    if 'UK' in choose:
        place_df = uk_choice_form('summary')
    elif 'US' in choose:
        place_df = us_choice_form('summary')
    elif 'World' in choose:
        place_df = world_choice_form('summary')

    try:
        summary = make_summary(place_df)
    except AttributeError:
        place_df = uk
        summary = make_summary(place_df)

    st.subheader(f'Latest data for {summary["place"]} as of {summary["date"]}')
    col1, col2, col3 = st.beta_columns([1, 1, 1])
    with col1:
        st.subheader('Cases')
        st.write(f'New Cases: {int(summary["newCases"])}')
        st.write(f'This is a change of {int(summary["case_diff"])} from seven days earlier')
        st.write(f'Total Cases: {int(summary["totalCases"])}')
    with col2:
        st.subheader('Deaths')
        st.write(f'New Deaths: {int(summary["newDeaths"])}')
        st.write(f'This is a change of {int(summary["death_diff"])} from seven days earlier')
        st.write(f'Total Deaths: {int(summary["totalDeaths"])}')
    with col3:
        st.subheader('Useful Statistics')
        if summary['vaccs']:
            st.write(f'{summary["vaccs"]:.1f}% of the population have been fully vaccinated')
        else:
            st.write('There is no data on vaccination')
        if summary['r']:
            st.write(f'The transmission rate (R) is {summary["r"]:.1f}')
        else:
            st.write('There is no data on transmission rate (R)')
        if summary['grow']:
            st.write(f'The growth rate is {summary["grow"]:.1f}')
    with st.beta_expander('View raw data:'):
        st.dataframe(place_df.sort_index(ascending=False))



