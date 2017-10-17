'''

Author: Matthew Turner <maturner01@gmail.com>

Date: April 01, 2017
'''
import numpy as np
import pandas as pd

from datetime import datetime
from rpy2.robjects.packages import importr

from rpy2 import robjects as ro
from rpy2.robjects import pandas2ri
pandas2ri.activate()
R = ro.r


# glmer = importr('lme4').glmer
lme = importr('lme4').lmer
lm = R.lm

extractAIC = importr('stats').extractAIC
coef = importr('stats').coef


DEFAULT_FIRST_DATES = [
    datetime(2016, 9, d) for d in range(20, 31)
] + [
    datetime(2016, 10, d) for d in range(1, 15)
]


DEFAULT_SECOND_DATES = [
    datetime(2016, 10, d) for d in range(15, 32)
] + [
    datetime(2016, 11, d) for d in range(1, 30)
]


def partition_AICs(df,
                   first_dates=DEFAULT_FIRST_DATES,
                   second_dates=DEFAULT_SECOND_DATES,
                   model_formula='count ~ phase + network + facet + (1|date)',
                   verbose=False
                   ):
    '''
    Given a dataframe with columns "date", "network", "facet", and "count",
    generates a dataframe with the AIC of each partition date.
    '''
    d = {
        'first_date': [],
        'second_date': [],
        'AIC': [],
        'coef': [],
        'model': []
    }

    for fd in first_dates:
        for sd in second_dates:

            d['first_date'].append(fd)
            d['second_date'].append(sd)

            if verbose:
                print('Calculating for d1={} & d2={}'.format(fd, sd))

            phase_df = add_phases(df, fd, sd)

            model = lm(
                model_formula,
                # family='poisson',
                data=phase_df
            )

            d['AIC'].append(extractAIC(model)[1])

            d['coef'].append(list(coef(model)))

            d['model'].append(model)



    return pd.DataFrame(d)


def add_phases(df,
               date1=datetime(2016, 9, 26),
               date2=datetime(2016, 10, 20)
               ):
    '''
    Create a dataframe with a new 'state' column
    '''

    phase = []
    ret = df.copy()

    for i, d in enumerate([d for d in df.date]):

        if date1 > d:
            # phase.append(1)
            phase.append('ground')

        elif date1 <= d and d <= date2:
            # phase.append(2)
            phase.append('elevated')

        else:
            # phase.append(3)
            phase.append('ground')

    ret['state'] = phase

    return ret


def relative_likelihood(aic_min, aic_other):
    return np.exp((aic_min - aic_other)/2.0)


class PartitionInfo:

    def __init__(self,
                 partition_date_1,
                 partition_date_2,
                 f_ground,
                 f_excited):

        self.partition_date_1 = partition_date_1
        self.partition_date_2 = partition_date_2
        self.f_ground = f_ground
        self.f_excited = f_excited

    @classmethod
    def from_fit(cls, fit):

        partition_date_1 = fit.first_date
        partition_date_2 = fit.second_date

        # R model returns the excited state freq as intercept b/c alphabetical
        f_excited = fit.coef[0]

        # the slope is the second coefficient; it will be negative if
        # hypothesis is correct
        f_ground = f_excited + fit.coef[1]

        return cls(partition_date_1, partition_date_2, f_ground, f_excited)


def partition_sums(counts_df, partition_infos):
    '''
    partition_infos should be a dictionary with 'MSNBCW', 'CNNW', 'FOXNEWSW',
    and 'All' as keys, with a PartitionInfo instance for each.
    '''
    ret = pd.DataFrame(
        index=['MSNBCW', 'CNNW', 'FOXNEWSW', 'All'],
        data=dict([('ground', np.zeros(4)), ('excited', np.zeros(4))])
    )
    ret = ret[['ground', 'excited']]

    cdf_index = counts_df.index

    counts_df = counts_df.copy()
    counts_df['All'] = counts_df.sum(axis=1)

    for network in ret.index:

        pd1 = partition_infos[network].partition_date_1
        pd2 = partition_infos[network].partition_date_2

        ground = counts_df.loc[
            (cdf_index < pd1) | (cdf_index > pd2), network
        ].sum()

        excited = counts_df.loc[
            (cdf_index >= pd1) & (cdf_index <= pd2), network
        ].sum()

        ret.loc[network] = [ground, excited]

    return ret
