#!/usr/bin/env python3

import json
from urllib.request import urlopen

import plotly.express as px

from graph_functions import var_readable


def make_geos(url):
    with urlopen(url) as response:
        geo = json.load(response)
    return geo


def get_geo_data(level):
    level_dict = {'us_counties': {'locs': 'fips',
                                  'feat_id': None,
                                  'name': 'US Counties'},
                  'us_states': {'locs': 'STATE',
                                'feat_id': 'properties.STATE',
                                'name': 'US States'},
                  'nation': {'locs': 'CTRY20CD',
                             'feat_id': 'properties.CTRY20CD',
                             'name': 'UK nations'},
                  'region': {'locs': 'RGN20CD',
                             'feat_id': 'properties.RGN20CD',
                             'name': 'England Regions'},
                  'utla': {'locs': 'areaCode',
                           'feat_id': 'properties.areaCode',
                           'name': 'UK upper tier local authorities'},
                  'ltla': {'locs': 'areaCode',
                           'feat_id': 'properties.areaCode',
                           'name': 'UK lower tier local authorities'},
                  'world': {'locs': 'ISO_A3',
                            'feat_id': 'properties.ISO_A3',
                            'name': 'the World'},
                  }

    locs = level_dict[level]['locs']
    feat_id = level_dict[level]['feat_id']
    name = level_dict[level]['name']

    return locs, feat_id, name


def get_map_settings(df, var):
    # for the scale
    maxi = df[var].max()
    mini = df[var].min()

    if 'growth' in var:
        color = px.colors.diverging.balance
        midpoint = 0
        hover = True
        color_range = None

    elif 'transmissionRate' in var:
        color = px.colors.diverging.balance
        midpoint = 1
        hover = ':.2f'
        color_range = None

    else:
        color = 'rainbow'
        midpoint = None
        color_range = [mini, maxi]
        if 'Per' in var or 'Rate' in var:
            hover = ':.2f'
        else:
            hover = ':.0f'

    return color, midpoint, color_range, hover


def make_uk_map(geo, df, var, date):  # TODO hackney and the city of london?
    if len(df['areaType'].unique()) > 1:
        return 'Error, input upper and lower LAs seperately'

    locs, feat_id, name = get_geo_data(df.areaType[0])

    df = df[['areaCode', 'areaName', var]].sort_index(ascending=False)
    color, midpoint, color_range, hover = get_map_settings(df, var)

    df = df.loc[f'{date}']

    df.rename(columns={'areaCode': locs}, inplace=True)

    fig = px.choropleth_mapbox(df,
                               geojson=geo,
                               locations=locs,
                               featureidkey=feat_id,
                               color=var,
                               color_continuous_scale=color,
                               color_continuous_midpoint=midpoint,
                               range_color=color_range,
                               mapbox_style='carto-positron',
                               opacity=0.5,
                               center={'lat': 55.2, 'lon': -3.4},
                               zoom=3.9,
                               labels={var: var_readable(var), 'areaName': 'Name'},
                               hover_name='areaName',
                               hover_data={locs: False,
                                           var: hover},
                               title=f'{var_readable(var)} in {name} as of {date.strftime("%d.%m.%Y")}',
                               height=700
                               )
    return fig


def make_us_map(geo, df, var, date, us_counties=False):
    if us_counties:
        locs, feat_id, name = get_geo_data('us_counties')
    else:
        locs, feat_id, name = get_geo_data('us_states')

    df = df[['fips', 'areaName', var]].sort_index(ascending=False).dropna(subset=[var])

    color, midpoint, color_range, hover = get_map_settings(df, var)

    df.rename(columns={'fips': locs}, inplace=True)

    if us_counties and var == 'population':
        df = df.loc['2021-06-01']
    else:
        df = df.loc[f'{date}']

    fig = px.choropleth_mapbox(df,
                               geojson=geo,
                               locations=locs,
                               featureidkey=feat_id,
                               color=var,
                               color_continuous_scale=color,
                               color_continuous_midpoint=midpoint,
                               range_color=color_range,
                               mapbox_style='carto-positron',
                               zoom=3,
                               center={"lat": 37.0902, "lon": -95.7129},
                               opacity=0.5,
                               labels={var: var_readable(var), 'areaName': 'Name'},
                               hover_name='areaName',
                               hover_data={locs: False,
                                           var: hover},
                               title=f'{var_readable(var)} in {name} as of {date.strftime("%d.%m.%Y")}',
                               height=700)

    return fig


def make_world_map(geo, df, var, date):
    if 'World' in df.areaName.unique():
        df.dropna(subset=['continent'])

    locs, feat_id, name = get_geo_data('world')

    df = df[['areaName', 'iso_code', var]].sort_index(ascending=False)

    if 'Weekly' in var:
        df[var] = df.groupby('iso_code')[var].bfill(limit=7)

    color, midpoint, color_range, hover = get_map_settings(df, var)

    if var in ['population', 'human_development_index', 'life_expectancy', 'hospital_beds_per_thousand',
               'handwashing_facilities', 'male_smokers', 'female_smokers', 'diabetes_prevalence',
               'cardiovasc_death_rate', 'extreme_poverty', 'gdp_per_capita', 'aged_70_older',
               'aged_65_older', 'median_age', 'population_density']:
        df = df.loc['2021-05-27']

    else:
        df = df.loc[f'{date}']

    df.rename(columns={'iso_code': locs}, inplace=True)

    fig = px.choropleth_mapbox(df,
                               geojson=geo,
                               locations=locs,
                               featureidkey=feat_id,
                               color=var,
                               color_continuous_scale=color,
                               color_continuous_midpoint=midpoint,
                               mapbox_style="carto-positron",
                               opacity=0.5,
                               zoom=-0.5,
                               title=f'{var_readable(var)} in the World as of {date.strftime("%d.%m.%Y")}',
                               labels={var: var_readable(var), 'areaName': 'Name'},
                               hover_name='areaName',
                               hover_data={locs: False,
                                           var: hover},
                               range_color=color_range,
                               height=700)

    return fig
