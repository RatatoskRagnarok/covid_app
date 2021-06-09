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
               '=cumCasesBySpecimenDateRate&format=csv'],
           'msoa': ['https://api.coronavirus.data.gov.uk/v2/data?areaType=msoa&metric'
                    '=newCasesBySpecimenDateRollingSum&metric=newCasesBySpecimenDateRollingRate&metric'
                    '=newCasesBySpecimenDateChange&metric=newCasesBySpecimenDateChangePercentage&metric'
                    '=newCasesBySpecimenDateDirection&format=csv']}


def get_uk_data(url_list):
    if len(url_list) == 1:
        df = pd.read_csv(url_list[0])
        return df
    else:
        for url in url_list:
            df = pd.read_csv(url_list[0])
            for i in range(len(url_list[1:])):
                extra = pd.read_csv(url_list[i+1])
                df = pd.merge(df, extra, how='outer')
        return df

