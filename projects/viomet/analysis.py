'''

Author: Matthew Turner <maturner01@gmail.com>

Date: April 01, 2017
'''
import numpy as np
import pandas as pd

from datetime import date
from rpy2.robjects.packages import importr

from rpy2 import robjects as ro
from rpy2.robjects import pandas2ri
pandas2ri.activate()
R = ro.r


# glmer = importr('lme4').glmer
lme = importr('lme4').lmer
lm = R.lm
extractAIC = importr('stats').extractAIC


DEFAULT_FIRST_DATES = [
    date(2016, 9, d) for d in range(20, 31)
] + [
    date(2016, 10, d) for d in range(1, 15)
]


DEFAULT_SECOND_DATES = [
    date(2016, 10, d) for d in range(15, 32)
] + [
    date(2016, 11, d) for d in range(1, 30)
]


def partition_AICs(df,
                   first_dates=DEFAULT_FIRST_DATES,
                   second_dates=DEFAULT_SECOND_DATES,
                   model_formula='count ~ phase + network + facet + (1|date)'
                   ):
    '''
    Given a dataframe with columns "date", "network", "facet", and "count",
    generates a dataframe with the AIC of each partition date.
    '''
    d = {'first_date': [], 'second_date': [], 'AIC': []}

    for fd in first_dates:
        for sd in second_dates:

            d['first_date'].append(fd)
            d['second_date'].append(sd)

            print('Calculating for d1={} & d2={}'.format(fd, sd))

            phase_df = add_phases(df, fd, sd)

            model = lm(
                model_formula,
                # family='poisson',
                data=phase_df
            )

            d['AIC'].append(extractAIC(model)[1])

    return pd.DataFrame(d)


def add_phases(df,
               date1=date(2016, 9, 26),
               date2=date(2016, 10, 20)
               ):
    '''
    Create a dataframe with a new 'phase' column
    '''

    phase = []
    ret = df.copy()

    for i, d in enumerate([d.date() for d in df.date]):

        if date1 > d:
            # phase.append(1)
            phase.append('ground')

        elif date1 <= d and d < date2:
            # phase.append(2)
            phase.append('elevated')

        else:
            # phase.append(3)
            phase.append('ground')

    ret['state'] = phase

    return ret


def relative_likelihood(aic_min, aic_other):
    return np.exp((aic_min - aic_other)/2.0)


def _count_by_start_localtime(df,
                              column_list=['program_name',
                                           'network',
                                           'facet_word']):
    '''
    Count the number of instances grouped by column_list. Adds a 'counts'
    column.

    Arguments:
        df (pandas.DataFrame): Analyzer.df attribute from Analyzer class
        column_list (list): list of columns on which to groupby then count

    Returns:
        (pandas.DataFrame) counts per start_localtime of tuples with types
            given in column_list
    '''
    all_cols = ['start_localtime'] + column_list

    subs = df[all_cols]

    c = subs.groupby(all_cols).size()

    ret_df = c.to_frame()
    ret_df.columns = ['counts']
    ret_df.reset_index(inplace=True)

    return ret_df

def count_by_timescale(timescale='D'):
    pass
