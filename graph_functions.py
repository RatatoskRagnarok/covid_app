#!/usr/bin/env python3

import re

import altair as alt
import pandas as pd
import streamlit as st

from df_functions import since_vaccines, since_vaccines_uk


def var_readable(col):
    if 'actuals.' in col or 'metrics.' in col:
        col = col[8:]
    if '.' in col:
        col = col.replace('.', ' ')
    if '_' in col:
        col = col.replace('_', ' ')
    if col == 'newDailyNsoDeaths':
        col = 'New Deaths with Covid-19 on the Death Certificate'
    else:
        res_list = re.findall('[a-zA-Z0-9][^A-Z1]*', col)
        col = ' '.join(res_list).title()
    return col


def get_name(df):
    name = df.iloc[0]['areaName']
    if name.startswith('United'):
        name = 'The ' + name
    return name


def uk_graph_options(df, key):
    time = st.selectbox('Choose a time to start the graph: ', ['Start of Covid', 'Vaccinations Started (2021)'],
                        key=key)
    if time == 'Vaccinations Started (2021)':
        vacc = True
    else:
        vacc = False
    if 'areaType' in df.columns:
        lockdowns = st.radio(
            'Select to show times of national lockdowns in red, and times in the tier system in green: ',
            ("Don't show", 'Show Lockdowns'), key=key)
        if lockdowns == 'Show Lockdowns':
            lockdowns = True
        else:
            lockdowns = False

        first_vacc = st.radio("Select to show the date of the UK's first vaccination: ", ("Don't show", 'Show'),
                              key=key)
        if first_vacc == "Show":
            first_vacc = True
        else:
            first_vacc = False
        return vacc, lockdowns, first_vacc


def graph_options(df, key):
    time = st.selectbox('Choose a time to start the graph: ', ['Start of Covid', 'Vaccinations Started (2021)'],
                        key=key)
    if time == 'Vaccinations Started (2021)':
        vacc = True
    else:
        vacc = False
    return vacc


def show_lockdown_areas(df, start_date='', vaccines=False):
    if not start_date:
        start_date = '2020-03-26'

    latest = str(df.index[0])[:10]  # TODO till we get out of actual lockdown!

    if vaccines:
        cutoff = pd.DataFrame({'start': ['2020-12-08', '2021-01-06'],
                               'stop': ['2021-01-06', latest],
                               'color': ['green', 'red']})
    else:
        cutoff = pd.DataFrame({'start': [start_date, '2020-06-23', '2020-11-05', '2020-12-02', '2021-01-06'],
                               'stop': ['2020-06-23', '2020-11-05', '2020-12-02', '2021-01-06', latest],
                               'color': ['red', 'green', 'red', 'green', 'red']})

    areas = alt.Chart(
            cutoff.reset_index()
        ).mark_rect(
            opacity=0.1
        ).encode(
            x='start:T',
            x2='stop:T',
            color=alt.Color('color:N', scale=None)
        )
    return areas


def show_vacc_line():
    vacc_rule = alt.Chart(pd.DataFrame(
            {'Date': ['2020-12-08'], 'color': ['black'], 'label': ['First UK Vaccination']})).mark_rule().encode(
            x='Date:T', color=alt.Color('color:N', scale=None))
    text = vacc_rule.mark_text(
            align='left',
            baseline='top',
            dx=7
        ).encode(
            text='label'
        )
    return vacc_rule + text


def new_stuff_graph(df, var, vaccines=False): # TODO sort for weekly variablesz
    if vaccines:
        if 'areaType' in df.columns:
            df = since_vaccines_uk(df)
        else:
            df = since_vaccines(df)

    var_string = var_readable(var)

    source = df[var].reset_index()
    source.rename(columns={'date': 'Date', var: var_string, 'index': 'Date'}, inplace=True)
    name = get_name(df)
    source.dropna()

    hover = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout")

    base = alt.Chart(source).encode(x=alt.X('Date:T', axis=alt.Axis(title='Date', format=" %d %b %Y"))).properties(title=f'{var_string} in {name})')

    bar = base.mark_bar(**{"opacity": 0.5}).encode(
        y=alt.Y(f'{var_string}:Q', axis=alt.Axis(title=f'{var_string}'))).interactive()

    line = base.mark_line(color='red').transform_window(rolling_mean=f'mean({var_string})', frame=[-4, 3]).encode(y='rolling_mean:Q')  # means don't need to calc rolling mean in df
    # more closely matches how uk gov calcs it

    points = line.transform_filter(hover).mark_circle()

    source2 = source.melt('Date')
    tooltips = alt.Chart(source2).transform_pivot("variable", "value", groupby=["Date"]).mark_rule().transform_window(rolling_mean=f'mean({var_string})', frame=[-4, 3]).encode(x='Date:T', opacity=alt.condition(hover, alt.value(0.3), alt.value(0)), tooltip=['Date:T', alt.Tooltip(f'{var_string}:Q'), alt.Tooltip('rolling_mean:Q', title='Weekly average', format='.0f')]).add_selection(hover).interactive()

    graph = bar + line + points + tooltips

    return graph.properties(width=700, height=500)


def uk_new_stuff_graph(df, var, vaccines=False, show_lockdowns=False, show_vaccines=False):
    graph = new_stuff_graph(df, var, vaccines)

    if show_vaccines:
        graph += show_vacc_line()

    if show_lockdowns:
        areas = show_lockdown_areas(df, vaccines=vaccines)
        graph += areas

    return graph.properties(width=600, height=500)


def many_var_one_place(df, var_list, vaccines=False):
    if vaccines:
        if 'areaType' in df.columns:
            df = since_vaccines_uk(df)
        else:
            df = since_vaccines(df)

    name = get_name(df)

    source = df[var_list].reset_index()
    for col in var_list:
        source.rename(columns={col: var_readable(col)}, inplace=True)
    source.rename(columns={'date': 'Date', 'index': 'Date'}, inplace=True)
    source.dropna()
    source = source.melt('Date')

    hover = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout")

    lines = alt.Chart(source).mark_line().transform_window(rolling_mean='mean(value)', frame=[-4, 3]).encode(
        x=alt.X('Date:T', axis=alt.Axis(title='Date', format=" %d %b %Y")),
        y=alt.Y('rolling_mean:Q', axis=alt.Axis(title='Number of People')),
        color='variable')

    points = lines.transform_filter(hover).mark_circle()

    tips_list = ['Date:T']
    tips_list += [f'{var_readable(x)}:Q' for x in var_list]

    tooltips = alt.Chart(source).transform_pivot("variable", "value", groupby=["Date"]).mark_rule().encode(
        x='Date:T', opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=tips_list).add_selection(hover).interactive()

    graph = lines + points + tooltips

    return graph.properties(width=700, height=500, title=f'Examining Several Variables in {name}')


def many_var_uk(df, var_list, vaccines=False, show_lockdowns=False, show_vaccines=False):
    if vaccines:
        df = since_vaccines_uk(df)

    name = get_name(df)

    graph = many_var_one_place(df, var_list, vaccines)

    if show_vaccines:
        graph += show_vacc_line()

    if show_lockdowns:
        areas = show_lockdown_areas(df, vaccines=vaccines)
        graph += areas

    return graph.properties(width=700, height=500, title=f'Examining Several Variables in {name}')


def uk_r_rate_graph(df, var, vaccines=False, show_lockdowns=False, show_vaccines=False):
    # no r rate info before this!
    df = df[df.index > '2020-05-30']

    name = get_name(df)

    if vaccines:
        df = since_vaccines_uk(df)
    if var == 'transmissionRate':
        var_list = [var, 'transmissionRateMin', 'transmissionRateMax']
    elif var == 'growthRate':
        var_list = [var, 'transmissionRateGrowthRateMin', 'transmissionRateGrowthRateMax']
    source = df[var_list].reset_index()

    if var == 'transmissionRate':
        source.rename(columns={'date': 'Date', 'transmissionRate': 'Transmission Rate (R)',
                               'transmissionRateMin': 'Minimum', 'transmissionRateMax': 'Maximum'}, inplace=True)
        var1 = 'Transmission Rate (R)'
    if var == 'growthRate':
        source.rename(columns={'date': 'Date', 'growthRate': 'Growth Rate',
                               'transmissionRateGrowthRateMin': 'Minimum', 'transmissionRateGrowthRateMax': 'Maximum'},
                      inplace=True)
        var1 = 'Growth Rate'

    source.dropna()

    hover = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout")

    area = alt.Chart(source).mark_area(**{"opacity": 0.5}).encode(
        x=alt.X('Date:T', axis=alt.Axis(title='Date', format=" %d %b %Y")),
        y=alt.Y('Minimum:Q', axis=alt.Axis(title=var1)), y2='Maximum:Q')

    line = alt.Chart(source).mark_line(color='red').encode(x='Date:T', y=f'{var1}:Q')

    points = line.transform_filter(hover).mark_circle()

    tips_list = ['Date:T', f'{var1}:Q', 'Maximum:Q', 'Minimum:Q']

    source2 = source.melt('Date')
    tooltips = alt.Chart(source2).transform_pivot("variable", "value", groupby=["Date"]).mark_rule().encode(
        x='Date:T', opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=tips_list).add_selection(hover).interactive()

    graph = line + area + tooltips + points

    if show_vaccines:
        graph += show_vacc_line()

    if show_lockdowns:
        areas = show_lockdown_areas(df, start_date='2020-05-30', vaccines=vaccines)
        graph += areas

    return graph.properties(width=700, height=500, title=f'{var1} in {name}')


def rate_graph(df, var, vaccines=False):
    name = get_name(df)

    if vaccines:
        if 'areaType' in df.columns:
            df = since_vaccines_uk(df)
        else:
            df = since_vaccines(df)

    if 'Weekly' in var:
        source = df[var].reset_index().bfill(limit=7)
    else:
        source = df[var].reset_index()

    if var == 'transmissionRate':
        source.rename(columns={'date': 'Date', 'transmissionRate': 'Transmission Rate (R)', 'index': 'Date'},
                      inplace=True)
        var1 = 'Transmission Rate (R)'
    elif var == 'testsPositiveRate':
        source.rename(
            columns={'date': 'Date', 'testsPositiveRate': 'Percentage of tests which are positive', 'index': 'Date'},
            inplace=True)
        var1 = 'Percentage of tests which are positive'
    else:
        source.rename(columns={'date': 'Date', var: var_readable(var), 'index': 'Date'}, inplace=True)
        var1 = var_readable(var)

    source.dropna(how='any')

    hover = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout")

    line = alt.Chart(source).mark_line(color='red').encode(
        x=alt.X('Date:T', axis=alt.Axis(title='Date', format=" %d %b %Y")),
        y=alt.Y(f'{var1}:Q', axis=alt.Axis(title=var1)))

    points = line.transform_filter(hover).mark_circle()

    source2 = source.melt('Date')
    tooltips = alt.Chart(source2).transform_pivot("variable", "value", groupby=["Date"]).mark_rule().encode(
        x='Date:T', opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=['Date:T', alt.Tooltip(f'{var1}:Q', format='.2f')]).add_selection(hover).interactive()

    graph = line + tooltips + points

    return graph.properties(width=700, height=500, title=f'{var1} in {name}')


def uk_rate_graph(df, var, vaccines=False, show_lockdowns=False, show_vaccines=False):
    name = get_name(df)
    if var == 'transmissionRate':
        var1 = 'Transmission Rate (R)'
    if var == 'testsPositiveRate':
        var1 = 'Percentage of tests which are positive'

    graph = rate_graph(df, var, vaccines)

    if show_vaccines:
        graph += show_vacc_line()

    if show_lockdowns:
        areas = show_lockdown_areas(df, start_date='2020-05-30', vaccines=vaccines)
        graph += areas

    return graph.properties(width=700, height=500, title=f'{var1} in {name}')


def multi_place_graph(multi_df, var, vaccines=False):
    if vaccines:
        multi_df = since_vaccines(multi_df)

    if 'Weekly' in var:
        source = multi_df[['areaName', var]].reset_index().bfill(limit=7)
    else:
        source = multi_df[['areaName', var]].reset_index()
    var_string = var_readable(var)

    source.rename(columns={'date': 'Date', var: var_string, 'areaName': 'Place', 'index': 'Date'}, inplace=True)
    source = source.round(2)
    source = source.dropna(subset=[var_string])

    hover = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout")

    lines = alt.Chart(source).mark_line().encode(x=alt.X('Date:T', axis=alt.Axis(title='Date', format=" %d %b %Y")),
                                                 y=f'{var_string}:Q', color='Place')

    points = lines.transform_filter(hover).mark_circle()

    tips_list = ['Date:T']
    tips_list += [f'{area}:Q' for area in source.Place.unique()]

    tooltips = alt.Chart(source).transform_pivot(
        "Place", var_string, groupby=["Date"]
    ).mark_rule().encode(
        x='Date:T',
        opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=tips_list
    ).add_selection(hover).interactive()

    graph = lines + points + tooltips

    return graph.properties(width=700, height=500, title=f'{var_string} in Several Places')

