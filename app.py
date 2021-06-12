#!/usr/bin/env python3

from datetime import date

import pandas as pd
import streamlit as st

from df_functions import prep_uk_df, prep_us_df, prep_world_df, make_summary
from get_data_functions import uk_dict
from graph_functions import var_readable, new_stuff_graph, uk_new_stuff_graph, many_var_uk, many_var_one_place, \
    uk_graph_options, uk_rate_graph, uk_r_rate_graph, rate_graph, graph_options, multi_place_graph

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


def choose_place(key):
    sel_1 = st.selectbox('Choose an option:', ['Somewhere in the UK',
                                               'Somewhere in the US',
                                               'Somewhere in the World'], key=key)
    if 'UK' in sel_1:
        st.write('Choose one of the following options:')
        uk_sel = st.selectbox('Choose the whole UK, a nation or region:', uk_places, key=key)
        st.write('OR')
        la_sel = st.selectbox('Choose a UK local authority:', [None]+la_places, key=key)

        if la_sel:
            return las[las.areaName == la_sel].dropna(how='all', axis=1)

        if uk_sel == 'UK' and la_sel is None:
            return uk
        elif uk_sel in nat.areaName.unique():
            return nat[nat.areaName == uk_sel]
        else:
            return reg[reg.areaName == uk_sel]

    elif 'US' in sel_1:
        us_sel = st.selectbox('Choose the whole US or a state:', us_places, key=key)
        st.write('OR')
        count_sel = st.selectbox('Choose a US county:', [None] + county_places, key=key)

        if count_sel:
            return counts[counts.areaName == count_sel].dropna(how='all', axis=1)
        elif us_sel == 'US':
            return us
        else:
            return states[states.areaName == us_sel].dropna(how='all', axis=1)

    elif 'World' in sel_1:
        world_sel = st.selectbox('Choose somewhere in the world:', world_places, index=225, key=key)
        return world[world.areaName == world_sel].dropna(how='all', axis=1)


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
    st.text('Case and death rates for UK areas are by specimen date and likely to be revised upwards')
    with st.beta_expander('Information on missing UK R rate data: '):
        st.text('The UK government stopped giving transmission rate (R) data for the whole UK in March 2021')
        st.text('Transmission rate (R) is available for individual nations in the UK')
        st.text('Or go to "World" and look at their UK entry.')

    with st.beta_expander('Click here to choose somewhere:'):
        place_df = choose_place('summary')
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

# graphs
with st.beta_container():
    st.header('Graphs')
    # one variable, one place graphs
    with st.beta_container():
        st.subheader('Graphs for one variable and one place at a time')
        with st.beta_expander('Click here to choose a place:'):
            place_df = choose_place('onevaroneplace')

        col1, col2 = st.beta_columns([1, 2])
        with col1:
            cols = ['newCases', 'newDeaths', 'newPeopleVaccinatedFirstDose', 'newPeopleVaccinatedComplete',
                    'hospitalCases',
                    'covidOccupiedICUBeds', 'newAdmissions', 'newAdmissionsWeekly', 'newIcuAdmissionsWeekly',
                    'testsPositiveRate', 'newDailyNsoDeaths', 'transmissionRate', 'growthRate']
            var_names = []
            for col in cols:
                if col in place_df.columns:
                    var_names.append(col)
            var = st.selectbox('Chose a variable: ', var_names, key='oneplacegraphs', format_func=var_readable)
            if 'areaType' in place_df.columns:
                vacc, lockdowns, first_vacc = uk_graph_options(place_df, 'onevaroneplace')
            else:
                vacc = graph_options(place_df, 'onevaroneplace')
        with col2:
            if 'areaType' in place_df.columns:
                if var == 'testsPositiveRate':
                    graph = uk_rate_graph(place_df, var, vaccines=vacc, show_vaccines=first_vacc,
                                          show_lockdowns=lockdowns)
                elif (var in ['transmissionRate', 'growthRate']) or ('Weekly' in var):
                    graph = uk_r_rate_graph(place_df, var, vaccines=vacc, show_vaccines=first_vacc,
                                            show_lockdowns=lockdowns)
                else:
                    graph = uk_new_stuff_graph(place_df, var, vaccines=vacc, show_lockdowns=lockdowns,
                                               show_vaccines=first_vacc)
            else:
                if (var in ['transmissionRate', 'testsPositiveRate', 'growthRate']) or ('Weekly' in var):
                    graph = rate_graph(place_df, var, vaccines=vacc)
                else:
                    graph = new_stuff_graph(place_df, var, vaccines=vacc)
            st.altair_chart(graph, use_container_width=True)
            with st.beta_expander('View raw data...'):
                st.dataframe(place_df[['areaName', var]].sort_index(ascending=False))

    # one place, many variables
    with st.beta_container():
        with st.beta_container():
            st.subheader('Compare several variables in one place')
            with st.beta_expander('Click here to choose a place:'):
                place_df = choose_place('manyvar')

            col1, col2 = st.beta_columns([1, 2])
            with col1:
                cols = ['hospitalCases', 'covidOccupiedICUBeds', 'newAdmissions', 'newCases', 'newDeaths',
                        'newPeopleVaccinatedFirstDose', 'newPeopleVaccinatedComplete', 'newDailyNsoDeaths',
                        'newAdmissionsWeekly',
                        'newIcuAdmissionsWeekly']
                var_names = []
                for col in cols:
                    if col in place_df.columns:
                        var_names.append(col)
                var_list = st.multiselect('Choose variables: ', var_names, default=['newCases', 'newDeaths'],
                                          format_func=var_readable)

                if 'areaType' in place_df.columns:
                    vacc, lockdowns, first_vacc = uk_graph_options(place_df, 'manyvar')
                else:
                    vacc = graph_options(place_df, 'manyvar')
            with col2:
                if 'areaType' in place_df.columns:
                    graph = many_var_uk(place_df, var_list, vaccines=vacc, show_lockdowns=lockdowns,
                                        show_vaccines=first_vacc)
                else:
                    graph = many_var_one_place(place_df, var_list, vaccines=vacc)
                st.altair_chart(graph, use_container_width=True)
                with st.beta_expander('View raw data...'):
                    var_list = ['areaName'] + var_list
                    st.dataframe(place_df[var_list].sort_index(ascending=False))

    # one variable several places graph
    with st.beta_container():
        st.subheader('Compare one variable in several places:')

        cols = ['newCasesPer100kPeople', 'newCasesPer100kPeopleWeekly', 'totalCasesPer100kPeople',
                'newDeathsPer100kPeople', 'totalDeathsPer100kPeople',
                'hospitalCasesPer100kPeople', 'newAdmissionsPer100kPeople', 'newAdmissionsPer100kPeopleWeekly',
                'covidOccupiedICUBedsPer100kPeople', 'newICUAdmissionsPer100kPeopleWeekly',
                'newTestsPer100kPeople', 'testsPositiveRate',
                'PeopleVaccinatedFirstDosePercentage', 'totalVaccinationCompleteCoveragePercentage',
                'transmissionRate', 'growthRate', 'lockdownScoreOutOf100', 'riskLevels']

        var = st.selectbox('Choose a variable: ', cols, format_func=var_readable)
        st.text('Choose places to compare')
        st.text('You can choose places from more than one list')
        st.text('Some places only have weekly data')
        st.text('If you want to compare the UK or the US with other countries, choose the versions in the "world" list')
        s1, s2, s3, s4, s5 = st.beta_columns(5)

        multi_places, multi_places2, multi_places3, multi_places4, multi_places5 = \
            [], False, False, False, []

        if var in uk.columns:
            multi_places.append('UK')
        uk_dfs = [nat, reg]
        for df in uk_dfs:
            if var in df.columns:
                multi_places += list(df.areaName.unique())
        if var in las.columns:
            multi_places2 = True
        if var in us.columns:
            multi_places3 = True
            multi_places4 = True
        if var in world.columns:
            for place in world.areaName.unique():
                thing = world[world.areaName == place].dropna(how='all', axis=1)
                if var in thing.columns:
                    multi_places5.append(place)
        df_list = []
        with s1:
            if multi_places:
                mplace1 = st.multiselect('Choose a place in the UK:', multi_places, default=['England'])
                for place in mplace1:
                    if place == 'UK':
                        df_list.append(uk)
                    if place in ['England', 'Scotland', 'Northern Ireland', 'Wales']:
                        df_list.append(nat[nat.areaName == place])
                    else:
                        df_list.append(reg[reg.areaName == place])
            else:
                st.write('No UK places have that data')
        with s2:
            if multi_places2:
                mplace2 = st.multiselect('Choose a UK local authority:', la_places)
                for place in mplace2:
                    df_list.append(las[las.areaName == place])
            else:
                st.write('No UK local authorities have that data')

        with s3:
            if multi_places3:
                mplace3 = st.multiselect('Choose a US state:', us_places, default=['New York'])
                for place in mplace3:
                    if place == 'United States':
                        df_list.append(us)
                    else:
                        df_list.append(states[states.areaName == place])
            else:
                st.write('No US state has that data')
        with s4:
            if multi_places4:
                mplace4 = st.multiselect('Choose a US county', county_places)
                for place in mplace4:
                    df_list.append(counts[counts.areaName == place])
            else:
                st.write('No US county has that data')
        with s5:
            if multi_places5:
                mplace5 = st.multiselect('Choose a place in the world:', multi_places5)
                for place in mplace5:
                    df_list.append(world[world.areaName == place])
            else:
                st.write('No world place has that data')

        col1, col2 = st.beta_columns([1, 2])
        with col1:
            vacc = graph_options(place_df, 'manyplacegraphs')
        with col2:
            if df_list:
                multi_df = pd.concat(df_list)
                graph = multi_place_graph(multi_df, var, vaccines=vacc)
            st.altair_chart(graph, use_container_width=True)
            with st.beta_expander('View raw data...'):
                var_list = ['areaName'] + var_list
                st.dataframe(multi_df[var_list].sort_index(ascending=False))

