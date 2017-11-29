'''

Author: Matthew Turner <maturner01@gmail.com>

Date: April 01, 2017
'''
import numpy as np
import pandas as pd

from collections import Counter
from datetime import datetime
from rpy2.robjects.packages import importr

from rpy2 import robjects as ro
from rpy2.robjects import pandas2ri

from projects.common import daily_metaphor_counts
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
                   verbose=False,
                   poisson=False
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

            if poisson:
                # Hacky, but need to transform to integer for poisson and
                # there are at most two shows on a day, so the fraction part
                # of frequency is 1/2 or 0.
                phase_df.freq *= 2
                model = lm(
                    model_formula,
                    family='poisson',
                    data=phase_df
                )
                d['coef'].append(list(coef(model)))
            else:
                model = lm(
                    model_formula,
                    data=phase_df
                )
                d['coef'].append(list(coef(model)))

            d['AIC'].append(extractAIC(model)[1])
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
            phase.append('ground')

        elif date1 <= d and d <= date2:
            phase.append('elevated')

        else:
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


def partition_info_table(partition_infos):
    index_keys = [('MSNBC', 'MSNBCW'),
                  ('CNN', 'CNNW'),
                  ('Fox News', 'FOXNEWSW')]
    columns = ['T_1e', 'T_Ne', 'fg', 'fe', 'r']
    data = []
    for ik in index_keys:
        key = ik[1]
        pi = partition_infos[key]
        data.append([pi.partition_date_1,
                     pi.partition_date_2,
                     pi.f_ground,
                     pi.f_excited,
                     pi.f_excited / pi.f_ground])

    index = [ik[0] for ik in index_keys]
    return pd.DataFrame(data=data, index=index, columns=columns).to_latex(
            formatters={'fg': '{:,.2f}'.format,
                        'fe': '{:,.2f}'.format,
                        'r': '{:,.2f}'.format
                        }
            )


def by_network_word_table(viomet_df,
                          date_range,
                          partition_infos,
                          words=['hit', 'beat', 'attack']
                          ):
    '''
    Second table in paper
    '''
    networks = ['MSNBC', 'CNN', 'Fox News']
    columns = ['fg', 'fe', 'total']

    # index_tuples = [(net, word) for net in networks for word in words]
    index_tuples = [(word, net) for word in words for net in networks]

    # index = pd.MultiIndex.from_tuples(
    #     index_tuples, names=['Network', 'Violent Word']
    # )
    index = pd.MultiIndex.from_tuples(
        index_tuples, names=['Violent Word', 'Network']
    )

    df = pd.DataFrame(index=index, columns=columns, data=0.0)

    def _get_ground(counts_df, netid, partition_infos, words):
        cdf = counts_df
        net_pi = partition_infos[netid]
        ground_dates = ((cdf.index < net_pi.partition_date_1) |
                        (cdf.index > net_pi.partition_date_2))

        ret = cdf[ground_dates][netid].sum()
        n_ground = Counter(ground_dates)[True]

        # Only take the indices of interest; these are 1D.
        return ret.loc[words], n_ground

    def _get_excited(counts_df, netid, partition_infos, words):
        cdf = counts_df
        net_pi = partition_infos[netid]

        excited_dates = ((cdf.index >= net_pi.partition_date_1) &
                         (cdf.index <= net_pi.partition_date_2))

        ret = cdf[excited_dates][netid].sum()
        n_excited = Counter(excited_dates)[True]
        # Only take the indices of interest; these are 1D.
        return ret.loc[words], n_excited

    counts_df = daily_metaphor_counts(
        viomet_df, date_range, by=['network', 'facet_word']
    )

    for idx, netid in enumerate(['MSNBCW', 'CNNW', 'FOXNEWSW']):

        sum_g, n_g = _get_ground(counts_df, netid, partition_infos, words)
        sum_e, n_e = _get_excited(counts_df, netid, partition_infos, words)

        freq_g = sum_g / n_g
        freq_e = sum_e / n_e

        totals = sum_g + sum_e

        network = networks[idx]
        for word in words:
            # df.loc[network, word] = [freq_g[word], freq_e[word], totals[word]]
            df.loc[word, network] = [freq_g[word], freq_e[word], totals[word]]

    fancy_columns = ['$f^g$', '$f^e$', 'total']
    df.columns = fancy_columns

    return df


def partition_sums(counts_df, partition_infos):
    '''
    partition_infos should be a dictionary with 'MSNBCW', 'CNNW', 'FOXNEWSW',
    and 'All' as keys, with a PartitionInfo instance for each.
    '''
    # if 'All' in partition_infos:
    #     index = ['MSNBCW', 'CNNW', 'FOXNEWSW', 'All']
    # else:
    #     index = ['MSNBCW', 'CNNW', 'FOXNEWSW']
    index = counts_df.columns
    print(index)

    index_len = len(index)
    ret = pd.DataFrame(
        index=index,
        data=dict(
            [('ground', np.zeros(index_len)), ('excited', np.zeros(index_len))]
        )
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
