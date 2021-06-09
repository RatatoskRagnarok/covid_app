#!/usr/bin/env python3

import re
from datetime import timedelta

import geopandas as gpd
import pandas as pd

from get_data_functions import get_uk_data, uk_dict


def make_population_df():
    """make a df of the codes, names and populations of areas"""
    df_pop = pd.read_csv(
        'https://raw.githubusercontent.com/RatatoskRagnarok/covid_app/master/data/pop_data/population.csv')
    df_pop = df_pop.dropna(how='all')
    return df_pop


def rename_columns(df):
    """renames the columns to make them more understandable"""
    old_columns = df.columns.values.tolist()
    new_columns = {}
    for col in old_columns:
        new_txt = ""
        for letter in col:
            new_txt += letter
        new_txt = new_txt.replace('cum', 'total')
        new_txt = new_txt.replace('ByPublishDate', '')
        new_txt = new_txt.replace('BySpecimenDate', '')
        new_txt = new_txt.replace('ByDeathDate', '')
        new_txt = new_txt.replace('28Days', '')
        new_txt = new_txt.replace('MV', 'Icu')
        new_txt = new_txt.replace('PillarOneTwo', '')
        new_txt = new_txt.replace('uniqueCasePositivityRollingSum', 'testsPositiveRate')
        new_txt = new_txt.replace('newCasesRollingRate', 'newCasesPer100kPeopleWeekly')
        new_txt = new_txt.replace('sRate', 'sPer100kPeople')
        new_columns[col] = new_txt
    df.rename(columns=new_columns, inplace=True)
    return df


def add_pop_to_df(df):
    """adds the population of places to the df"""
    df_pop = make_population_df()
    pop_dict = {}
    areas = df.areaCode.unique()
    for area in areas:
        population = (df_pop[df_pop['areaCode'] == area]).iloc[0]['population']
        population = population.replace(',', '')
        pop_dict[area] = int(population)
    df['population'] = df['areaCode'].map(pop_dict)
    return df


def prep_uk_df(url_list):
    df = get_uk_data(url_list)
    df = rename_columns(df)
    df = add_pop_to_df(df)

    # getting mean for transmission rate and growth rate
    if 'transmissionRateMax' in df.columns and df.areaName[0] != 'United Kingdom':
        df['transmissionRate'] = df[['transmissionRateMin', 'transmissionRateMax']].mean(axis=1)
        df['growthRate'] = df[['transmissionRateGrowthRateMax', 'transmissionRateGrowthRateMin']].mean(axis=1)
        # back filling values
        for col in ['transmissionRate', 'growthRate', 'transmissionRateMin', 'transmissionRateMax',
                    'transmissionRateGrowthRateMax', 'transmissionRateGrowthRateMin']:
            df[col] = df.groupby('areaName')[col].bfill(limit=7)

    # getting tests positive rate
    if 'newTests' in df.columns:
        df['testsPositiveRate'] = (df.newCases / df.newTests) * 100
        df['testsPositiveRate'] = df.groupby('areaCode')['testsPositiveRate'].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # getting per 100k people rates
    for col in ['newCases', 'newDeaths', 'hospitalCases', 'covidOccupiedIcuBeds', 'newAdmissions']:
        if col in df.columns:
            df[f'{col}Per100kPeople'] = (df[col] / df.population) * 100000
            df[f'{col}Per100kPeople'] = df.groupby('areaCode')[f'{col}Per100kPeople'].transform(lambda s: s.rolling(7, min_periods=1).mean())
    if 'newTests' in df.columns:
        df['newTestsPer100kPeople'] = (df.newTests / df.population) * 100000

    # percentage of people had first dose
    if 'totalPeopleVaccinatedFirstDose' in df.columns:
        df['peopleVaccinatedFirstDosePercentage'] = (df.totalPeopleVaccinatedFirstDose / df.population) * 100

    # change name of outer hebrides place
    df.areaName.replace({'Na h-Eileanan Siar': 'Comhairle nan Eilean Siar'}, inplace=True)

    df.dropna(how='all', axis=1, inplace=True)
    return df
