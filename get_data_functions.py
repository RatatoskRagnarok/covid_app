#!/usr/bin/env python3

import pandas as pd
import streamlit as st

uk_dict = {'uk': ['https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric=newCasesBySpecimenDate&metric'
                  '=cumCasesBySpecimenDateRate&metric=cumCasesBySpecimenDate&metric=newDeaths28DaysByDeathDate&metric'
                  '=cumDeaths28DaysByDeathDate&format=csv',
                  'https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric'
                  '=cumDeaths28DaysByDeathDateRate&metric=newAdmissions&metric=cumAdmissions&metric'
                  '=covidOccupiedMVBeds&metric=hospitalCases&format=csv',
                  'https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric'
                  '=newCasesBySpecimenDateRollingRate&metric=newDailyNsoDeathsByDeathDate&metric'
                  '=cumPeopleVaccinatedFirstDoseByPublishDate&metric'
                  '=cumVaccinationCompleteCoverageByPublishDatePercentage&metric'
                  '=newPeopleVaccinatedCompleteByPublishDate&format=csv',
                  'https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric'
                  '=newPeopleVaccinatedFirstDoseByPublishDate&metric=cumPeopleVaccinatedCompleteByPublishDate&metric'
                  '=newPeopleVaccinatedCompleteByPublishDate&metric=newPeopleVaccinatedSecondDoseByPublishDate&metric'
                  '=newPillarOneTwoTestsByPublishDate&format=csv',
                  'https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric'
                  '=cumPeopleVaccinatedSecondDoseByPublishDate&format=csv'],
           'nation': ['https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric=newCasesBySpecimenDate'
                      '&metric=cumCasesBySpecimenDateRate&metric=cumCasesBySpecimenDate&metric'
                      '=newDeaths28DaysByDeathDate&metric=cumDeaths28DaysByDeathDate&format=csv',
                      'https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric'
                      '=cumDeaths28DaysByDeathDateRate&metric=newAdmissions&metric=cumAdmissions&metric'
                      '=covidOccupiedMVBeds&metric=hospitalCases&format=csv',
                      'https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric'
                      '=transmissionRateGrowthRateMax&metric=transmissionRateGrowthRateMin&metric=transmissionRateMax'
                      '&metric=transmissionRateMin&metric=newCasesBySpecimenDateRollingRate&format=csv',
                      'https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric'
                      '=newDailyNsoDeathsByDeathDate&metric=newDeaths28DaysByDeathDateRollingRate&metric'
                      '=cumVaccinationCompleteCoverageByPublishDatePercentage&metric'
                      '=newPeopleVaccinatedCompleteByPublishDate&metric=newPeopleVaccinatedFirstDoseByPublishDate'
                      '&format=csv',
                      'https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric'
                      '=newPeopleVaccinatedSecondDoseByPublishDate&metric=cumPeopleVaccinatedCompleteByPublishDate'
                      '&metric=cumPeopleVaccinatedFirstDoseByPublishDate&metric'
                      '=cumPeopleVaccinatedSecondDoseByPublishDate&metric'
                      '=uniqueCasePositivityBySpecimenDateRollingSum&format=csv'],
           'region': ['https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric=newCasesBySpecimenDate'
                      '&metric=cumCasesBySpecimenDateRate&metric=cumCasesBySpecimenDate&metric'
                      '=newDeaths28DaysByDeathDate&metric=cumDeaths28DaysByDeathDate&format=csv',
                      'https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric'
                      '=cumDeaths28DaysByDeathDateRate&metric=newCasesBySpecimenDateRollingRate&metric'
                      '=newDailyNsoDeathsByDeathDate&metric=newDeaths28DaysByDeathDateRollingRate&metric'
                      '=uniqueCasePositivityBySpecimenDateRollingSum&format=csv'],
           'utla': [
               'https://api.coronavirus.data.gov.uk/v2/data?areaType=utla&metric=cumCasesBySpecimenDate&metric'
               '=newCasesBySpecimenDate&metric=newDeaths28DaysByDeathDate&metric'
               '=uniqueCasePositivityBySpecimenDateRollingSum&metric=cumDeaths28DaysByDeathDate&format=csv',
               'https://api.coronavirus.data.gov.uk/v2/data?areaType=utla&metric=cumCasesBySpecimenDate&metric'
               '=cumCasesBySpecimenDateRate&format=csv'],
           'ltla': [
               'https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla&metric=cumCasesBySpecimenDate&metric'
               '=newCasesBySpecimenDate&metric=newDeaths28DaysByDeathDate&metric'
               '=uniqueCasePositivityBySpecimenDateRollingSum&metric=cumDeaths28DaysByDeathDate&format=csv',
               'https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla&metric=cumCasesBySpecimenDate&metric'
               '=cumCasesBySpecimenDateRate&format=csv']}


def get_uk_data(url_list):
    if len(url_list) == 1:
        df = pd.read_csv(url_list[0])
        return df
    else:
        for url in url_list:
            df = pd.read_csv(url_list[0])
            for i in range(len(url_list[1:])):
                extra = pd.read_csv(url_list[i + 1])
                df = pd.merge(df, extra, how='outer')
        return df


def get_us_data(us=False, state=False, county=False):
    api_key = '0bc451cc1130432d857a2643b60f0ba0'
    if us:
        us_url = f'https://api.covidactnow.org/v2/country/US.timeseries.csv?apiKey={api_key}'
        return pd.read_csv(us_url, dtype={"fips": str})
    if state:
        state_url = f'https://api.covidactnow.org/v2/states.timeseries.csv?apiKey={api_key}'
        return pd.read_csv(state_url, dtype={"fips": str})
    if county:
        count_url = f'https://api.covidactnow.org/v2/counties.timeseries.csv?apiKey={api_key}'
        cols = ['date', 'state', 'county', 'fips', 'actuals.cases', 'actuals.newCases', 'metrics.infectionRate',
                'metrics.testPositivityRatio', 'metrics.caseDensity', 'actuals.icuBeds.currentUsageCovid',
                'actuals.hospitalBeds.currentUsageCovid', 'actuals.vaccinationsInitiated', 'actuals.vaccinationsCompleted',
                'metrics.vaccinationsCompletedRatio', 'actuals.newDeaths', 'actuals.deaths', 'riskLevels.overall',
                'metrics.vaccinationsInitiatedRatio']
        return pd.read_csv(count_url, dtype={"fips": str}, usecols=cols)
