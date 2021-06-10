#!/usr/bin/env python3

import re
from datetime import timedelta

import geopandas as gpd
import pandas as pd

from get_data_functions import get_uk_data, uk_dict, get_us_data


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
    # remove empty columns
    df = df.dropna(axis=1, how='all')
    # remove empty rows
    df = df.dropna(how='all')
    df.date = pd.to_datetime(df.date)
    df.set_index('date', inplace=True)

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
        df['testsPositiveRate'] = df.groupby('areaCode')['testsPositiveRate'].transform(
            lambda s: s.rolling(7, min_periods=1).mean())

    # getting per 100k people rates
    for col in ['newCases', 'newDeaths', 'hospitalCases', 'covidOccupiedIcuBeds', 'newAdmissions']:
        if col in df.columns:
            df[f'{col}Per100kPeople'] = (df[col] / df.population) * 100000
            df[f'{col}Per100kPeople'] = df.groupby('areaCode')[f'{col}Per100kPeople'].transform(
                lambda s: s.rolling(7, min_periods=1).mean())
    if 'newTests' in df.columns:
        df['newTestsPer100kPeople'] = (df.newTests / df.population) * 100000

    # percentage of people had first dose
    if 'totalPeopleVaccinatedFirstDose' in df.columns:
        df['peopleVaccinatedFirstDosePercentage'] = (df.totalPeopleVaccinatedFirstDose / df.population) * 100

    # change name of outer hebrides place
    df.areaName.replace({'Na h-Eileanan Siar': 'Comhairle nan Eilean Siar'}, inplace=True)

    df.dropna(how='all', axis=1, inplace=True)
    return df


def prep_msoa():
    df = pd.read_csv('https://api.coronavirus.data.gov.uk/v2/data?areaType=msoa&metric'
                     '=newCasesBySpecimenDateRollingSum&metric=newCasesBySpecimenDateRollingRate&metric'
                     '=newCasesBySpecimenDateChange&metric=newCasesBySpecimenDateChangePercentage&metric'
                     '=newCasesBySpecimenDateDirection&format=csv')
    # remove empty columns
    df = df.dropna(axis=1, how='all')
    # remove empty rows
    df = df.dropna(how='all')
    df.date = pd.to_datetime(df.date)
    df.set_index('date', inplace=True)
    df['areaName2'] = df.areaName + ', ' + df.UtlaName
    old_columns = df.columns.values.tolist()
    new_columns = {}
    for col in old_columns:
        new_columns[col] = col.replace('BySpecimenDate', '').replace('RollingRate', 'Per100kPeopleWeekly')
    df.rename(columns=new_columns, inplace=True)
    return df


def prep_us_df(us=False, state=False, county=False):
    """

    Args:
        us: a flag, choose only one to be true
        state: a flag, choose only one to be true
        county: a flag, choose only one to be true

    Returns: finished dataframe for either US, states or counties

    """
    df = get_us_data(us, state, county)
    # remove empty columns
    df = df.dropna(axis=1, how='all')
    # remove empty rows
    df = df.dropna(how='all')
    # convert date to datetime and set it to index
    df.date = pd.to_datetime(df.date)
    df.set_index('date', inplace=True)

    if us:
        df['areaName'] = 'United States'
        df['population'] = 331002647.0

    if state:
        state_pop = pd.read_csv('https://raw.githubusercontent.com/RatatoskRagnarok/covid_app/master/data/pop_data'
                                '/US_state_pop.csv',
                                dtype={"fips": str})
        df = pd.merge(df.reset_index(), state_pop[['state', 'state_name', 'population']],
                      on='state', how='outer').set_index('date')
        df = df.rename(columns={'state_name': 'areaName'})
        # add in the Northern Mariana Islands
        df.areaName.fillna('Northern Mariana Islands', inplace=True)

    if county:
        county_pop = pd.read_csv('https://raw.githubusercontent.com/RatatoskRagnarok/covid_app/master/data/pop_data'
                                 '/US_county_pop.csv',
                                 dtype={'geo_id': str})
        county_pop = county_pop.rename(columns={'geo_id': 'fips'})
        df = pd.merge(df.reset_index(), county_pop[['fips', 'state_name', 'population']],
                      on='fips', how='left').set_index('date')
        df['areaName'] = df.county + ', ' + df.state_name

    # rename us columns
    us_to_uk_names = {
        'actuals.cases': 'totalCases',
        'actuals.newCases': 'newCases',
        'metrics.infectionRate': 'transmissionRate',
        'metrics.testPositivityRatio': 'testsPositiveRate',
        'metrics.caseDensity': 'newCasesPer100kPeople',
        'actuals.icuBeds.currentUsageCovid': 'covidOccupiedIcuBeds',
        'actuals.hospitalBeds.currentUsageCovid': 'hospitalCases',
        'actuals.vaccinationsInitiated': 'totalPeopleVaccinatedFirstDose',
        'actuals.vaccinationsCompleted': 'totalPeopleVaccinatedComplete',
        'metrics.vaccinationsCompletedRatio': 'totalVaccinationCompleteCoveragePercentage',
        'actuals.newDeaths': 'newDeaths',
        'actuals.deaths': 'totalDeaths',
        'riskLevels.overall': 'riskLevels',
        'metrics.vaccinationsInitiatedRatio': 'peopleVaccinatedFirstDosePercentage'
    }

    df = df.rename(columns=us_to_uk_names)

    # calculating new people vaccinated cos only given totals
    df['newPeopleVaccinatedFirstDose'] = df.totalPeopleVaccinatedFirstDose - df.totalPeopleVaccinatedFirstDose.shift(1)
    df['newPeopleVaccinatedComplete'] = df.totalPeopleVaccinatedComplete - df.totalPeopleVaccinatedComplete.shift(1)

    # calculating rates per 100k people
    for col in ['newDeaths', 'hospitalCases', 'covidOccupiedIcuBeds', 'totalCases', 'totalDeaths']:
        if col in df.columns:
            df[f'{col}Per100kPeople'] = (df[col] / df.population) * 100000
            df[f'{col}Per100kPeople'] = df.groupby('fips')[f'{col}Per100kPeople'].transform(
                lambda s: s.rolling(7, min_periods=1).mean())

    # calculating percentage
    df.peopleVaccinatedFirstDosePercentage *= 100
    # changing percentage to match others
    df.totalVaccinationCompleteCoveragePercentage *= 100
    # to turn it into a percentage
    df.testsPositiveRate *= 100

    # calculating testing rate per 100k
    if 'actuals.positiveTests' in df.columns:
        df['newTestsPer100kPeople'] = ((df['actuals.positiveTests'] + df['actuals.negativeTests']) / df.population) * 100000

    df.dropna(subset=['areaName'], inplace=True)

    return df


def prep_world_df():
    df = pd.read_csv('https://covid.ourworldindata.org/data/owid-covid-data.csv')
    # remove empty columns
    df = df.dropna(axis=1, how='all')
    # remove empty rows
    df = df.dropna(how='all')
    # convert date to datetime and set it to index
    df.date = pd.to_datetime(df.date)
    df.set_index('date', inplace=True)

    # renaming columns to match uk
    world_to_uk_names = {
        'location': 'areaName',
        'total_cases': 'totalCases',
        'new_cases': 'newCases',
        'total_deaths': 'totalDeaths',
        'new_deaths': 'newDeaths',
        'reproduction_rate': 'transmissionRate',
        'icu_patients': 'covidOccupiedIcuBeds',
        'hosp_patients': 'hospitalCases',
        'positive_rate': 'testsPositiveRate',
        'people_vaccinated': 'totalPeopleVaccinatedFirstDose',
        'people_fully_vaccinated': 'totalPeopleVaccinatedComplete',
        'weekly_icu_admissions': 'newIcuAdmissionsWeekly',
        'stringency_index': 'lockdownScoreOutOf100',
        'new_tests': 'newTests',
        'weekly_hosp_admissions': 'newAdmissionsWeekly'
    }

    df = df.rename(columns=world_to_uk_names)
    # calculating new people vaccinated cos only given totals
    df['newPeopleVaccinatedFirstDose'] = df.totalPeopleVaccinatedFirstDose - df.totalPeopleVaccinatedFirstDose.shift(1)
    df['newPeopleVaccinatedComplete'] = df.totalPeopleVaccinatedComplete - df.totalPeopleVaccinatedComplete.shift(1)
    # calculating percentage
    df['peopleVaccinatedFirstDosePercentage'] = (df.totalPeopleVaccinatedFirstDose / df.population) * 100
    df['totalVaccinationCompleteCoveragePercentage'] = (df.totalPeopleVaccinatedComplete / df.population) * 100
    # to turn it into a percentage
    df.testsPositiveRate *= 100

    # changing millions to 100ks
    df['newCasesPer100kPeople'] = df.new_cases_smoothed_per_million / 10
    df['newDeathsPer100kPeople'] = df.new_deaths_smoothed_per_million / 10
    df['hospitalCasesPer100kPeople'] = df.hosp_patients_per_million / 10
    df['covidOccupiedIcuBedsPer100kPeople'] = df.icu_patients_per_million / 10
    df['newAdmissionsPer100kPeopleWeekly'] = df.weekly_hosp_admissions_per_million / 10
    df['newIcuAdmissionsPer100kPeopleWeekly'] = df.weekly_icu_admissions_per_million / 10
    df['totalCasesPer100kPeople'] = df.total_cases_per_million / 10
    df['totalDeathsPer100kPeople'] = df.total_deaths_per_million / 10

    # changing 1000s to 100000
    df['newTestsPer100kPeople'] = df.new_tests_smoothed_per_thousand * 100

    # add missing stationary variables for map
    tkm = pd.Series(data={'iso_code': 'TKM',
                          'areaName': 'Turkmenistan',
                          'continent': 'Asia',
                          'population': 6031187.0,
                          'human_development_index': 0.715,
                          'life_expectancy': 68.19,
                          'hospital_beds_per_thousand': 7.4,
                          'handwashing_facilities': 100.0,
                          'diabetes_prevalence': 7.11,
                          'cardiovasc_death_rate': 536.783,
                          'gdp_per_capita': 16389.023,
                          'aged_70_older': 2.541,
                          'aged_65_older': 4.277,
                          'median_age': 26.9,
                          'population_density': 12.253},
                    name=pd.to_datetime('2021-05-27'))

    shn = pd.Series(data={'iso_code': 'SHN',
                          'areaName': 'Saint Helena',
                          'continent': 'Asia',
                          'population': 6071.0,
                          'life_expectancy': 80.56},
                    name=pd.to_datetime('2021-05-27'))

    nru = pd.Series(data={'iso_code': 'NRU',
                          'areaName': 'Nauru',
                          'continent': 'Oceania',
                          'population': 10834.0,
                          'life_expectancy': 59.96,
                          'hospital_beds_per_thousand': 5.0,
                          'male_smokers': 36.9,
                          'female_smokers': 43.0,
                          'diabetes_prevalence': 24.07,
                          'gdp_per_capita': 12895.635,
                          'population_density': 682.45},
                    name=pd.to_datetime('2021-05-27'))

    flk = pd.Series(data={'iso_code': 'FLK',
                          'areaName': 'Falkland Islands',
                          'continent': 'South America',
                          'population': 3483.0,
                          'life_expectancy': 81.44},
                    name=pd.to_datetime('2021-05-27'))

    bes = pd.Series(data={'iso_code': 'BES',
                          'areaName': 'Bonaire Sint Eustatius and Saba',
                          'continent': 'North America',
                          'population': 26221.0,
                          'life_expectancy': 77.79},
                    name=pd.to_datetime('2021-05-27'))
    extra = pd.concat([bes, flk, nru, shn, tkm], axis=1).T

    cols = extra.columns[3:]
    extra[cols] = extra[cols].apply(pd.to_numeric)

    df = pd.concat([df, extra])

    # filling in missing bits
    df['lockdownScoreOutOf100'] = df.groupby('iso_code')['lockdownScoreOutOf100'].ffill(limit=7)

    return df