'''

Author: Matthew Turner <maturner01@gmail.com>

Date: April 01, 2017
'''
import numpy as np
import pandas as pd

from collections import Counter
from datetime import datetime
from functools import reduce

from rpy2.robjects.packages import importr
from rpy2 import robjects as ro
from rpy2.robjects import pandas2ri

from app.models import IatvCorpus
from projects.common import (
    daily_frequency, daily_metaphor_counts, get_project_data_frame
)

pandas2ri.activate()
R = ro.r


# glmer = importr('lme4').glmer
lme = importr('lme4').lmer
lm = R.lm

extractAIC = importr('stats').extractAIC
coef = importr('stats').coef


def get_pvalue(model):
    return importr('base').summary(model).rx2('coefficients')[-1]


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
                   candidate_excited_date_pairs=[()],
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
        'last_date': [],
        'AIC': [],
        'coef': [],
        'model': []
    }

    for first_date, last_date in candidate_excited_date_pairs:

        phase_df = add_phases(df, first_date, last_date)

        # If there are not two states (ground and excited), don't model.
        # This happens when neither first or last is in the df.date column
        # or if the excited state takes up all available dates, e.g. 9-1 to
        # 11-29 and there is no data for 11-30.
        if (len(phase_df.state.unique()) < 2
                or np.sum(phase_df.state == 'excited') < 10):

            continue

        d['first_date'].append(first_date)
        d['last_date'].append(last_date)

        if verbose:
            print(
                'Calculating for d1={} & d2={}'.format(first_date, last_date)
            )

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


def add_phases(df, date1=datetime(2016, 9, 26),
               date2=datetime(2016, 10, 20)):
    '''
    Create a dataframe with a new 'state' column
    '''

    phase = []
    ret = df.copy()

    # XXX super confusing with all the "date"s floating around.
    for i, d in enumerate([d for d in df.date]):

        if date1.date() > d.date():
            phase.append('ground')

        elif date1.date() <= d.date() and d.date() <= date2.date():
            phase.append('excited')

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
        partition_date_2 = fit.last_date

        # R model returns the excited state freq as intercept b/c alphabetical
        f_excited = fit.coef[0]

        # The slope is the second coefficient; it will be negative if
        # hypothesis is correct.
        f_ground = f_excited + fit.coef[1]

        return cls(partition_date_1, partition_date_2, f_ground, f_excited)


def partition_info_table(viomet_df,
                         date_range,
                         partition_infos):
    '''
    TODO
    '''
    index_keys = [('MSNBC', 'MSNBCW'),
                  ('CNN', 'CNNW'),
                  ('Fox News', 'FOXNEWSW')]

    columns = ['$t_0^{(2)}$', '$t^{(2)}_{N^{(2)}}$', '$f^{(1)}$',
               '$f^{(2)}$', 'reactivity', 'total uses']

    counts_df = daily_metaphor_counts(
        viomet_df, date_range, by=['network']
    )

    data = []
    for ik in index_keys:
        key = ik[1]
        pi = partition_infos[key]
        data.append([
            pi.partition_date_1,
            pi.partition_date_2,
            pi.f_ground,
            pi.f_excited,
            ((pi.f_excited - pi.f_ground) / pi.f_ground),
            counts_df[key].sum()
        ])

    index = [ik[0] for ik in index_keys]

    return pd.DataFrame(data=data, index=index, columns=columns)


def by_network_word_table(viomet_df,
                          date_range,
                          partition_infos,
                          words=['hit', 'beat', 'attack']
                          ):
    '''
    Second table in paper
    '''
    networks = ['MSNBC', 'CNN', 'Fox News']
    columns = ['fg', 'fe', 'reactivity', 'total uses']

    # index_tuples = [(net, word) for net in networks for word in words]
    index_tuples = [(word, net) for word in words for net in networks]

    index = pd.MultiIndex.from_tuples(
        index_tuples, names=['Violent Word', 'Network']
    )

    df = pd.DataFrame(index=index, columns=columns, data=0.0)

    counts_df = daily_metaphor_counts(
        viomet_df, date_range, by=['network', 'facet_word']
    )

    for idx, netid in enumerate(['MSNBCW', 'CNNW', 'FOXNEWSW']):

        sum_g, n_g = _get_ground(
            counts_df, netid, partition_infos, words=words
        )
        sum_e, n_e = _get_excited(
            counts_df, netid, partition_infos, words=words
        )

        freq_g = sum_g / n_g
        freq_e = sum_e / n_e

        reactivity = ((freq_e - freq_g) / freq_g)

        totals = sum_g + sum_e

        network = networks[idx]
        for word in words:
            df.loc[word, network] = [
                freq_g[word], freq_e[word], reactivity[word], totals[word]
            ]

    fancy_columns = ['$f^{(1)}$', '$f^{(2)}$', 'reactivity', 'total uses']
    df.columns = fancy_columns

    return df


def model_fits_table(viomet_df, date_range, network_fits, top_n=10):
    '''
    Relative ikelihoods of null model vs the best dynamic model fit and
    greater-AIC dynamic model fits vs the best dynamic model fit.

    Arguments:
        network_fits (dict): keyed by network, values are lists where the
            last element in the list is the dataframe of alternate
            start and end dates with AIC values of the associated
            fitted model. TODO: improve network_fits setup; it's opaque,
            each value of that dict is a list with three elements I think.
        top_n (int): number of top-performing models by relative likelihood
            to include in table.
    '''

    networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']
    ret = {}

    for network in networks:
        network_df = network_fits[network][-1]

        # Need to extract minimum AIC as the best; likelihood relative to it.
        low = network_df.AIC.min()
        network_df.loc[:, 'rl'] = relative_likelihood(low, network_df.AIC)

        # The least AIC min has a relative likelihood of 1.0; remove it.
        # network_df = network_df[network_df.rl != 1.0]
        network_df.sort_values('rl', ascending=False, inplace=True)

        # If there are exact duplicates of relative likelihood it's due to
        # there not being data between one of the candidate partition dates.
        network_df.drop_duplicates(subset='rl', inplace=True)

        network_df = network_df.iloc[:top_n]
        network_df['pvalue'] = [
            get_pvalue(model) for model in list(network_df.model)
        ]

        # Multiply by -1.0 b/c excited
        # treated as "less" than ground due to alpha ordering in R.
        # c1 is the ``excited'' region frequency, which is really just the
        # second region; c2 is ground frequency - excited frequency. Thus
        # c1 + c2 = ground frequency.
        network_df['reactivity'] = [
            -1.0 * (c2 / (c1 + c2)) for c1, c2 in network_df['coef']
        ]

        ret_df = network_df[
            ['rl', 'first_date', 'last_date', 'reactivity', 'pvalue']
        ]
        ret_df.columns = [
            'rel. lik.', '$t_0^{(2)}$', '$t^{(2)}_{N^{(2)}}$',
            'reactivity', '$P(<|t|)$'
        ]

        ret.update({network: ret_df})

    return ret


def by_network_subj_obj_table(viomet_df,
                              date_range,
                              partition_infos,
                              subjects=['Barack Obama', 'Mitt Romney'],
                              objects=['Barack Obama', 'Mitt Romney']):
    '''
    TODO
    '''
    networks = ['MSNBC', 'CNN', 'Fox News']
    columns = ['fg', 'fe', 'reactivity', 'total uses']

    # index_tuples = [(net, word) for net in networks for word in words]
    subj_objs = ["Subject=" + subj for subj in subjects] \
        + ["Object=" + obj for obj in objects]
    index_tuples = [(so, net) for so in subj_objs for net in networks]

    index = pd.MultiIndex.from_tuples(
        index_tuples, names=['Subject/Object', 'Network']
    )

    df = pd.DataFrame(index=index, columns=columns, data=0.0)

    # Next two blocks support more than two subjects or objects.
    subject_rows = reduce(
        lambda x, y: (viomet_df.subjects == x) | (viomet_df.subjects == y),
        subjects
    )
    object_rows = reduce(
        lambda x, y: (viomet_df.objects == x) | (viomet_df.objects == y),
        objects
    )
    subject_df = viomet_df[subject_rows]
    object_df = viomet_df[object_rows]

    subject_counts_df = daily_metaphor_counts(
        subject_df, date_range, by=['network', 'subjects'],
    )
    object_counts_df = daily_metaphor_counts(
        object_df, date_range, by=['network', 'objects']
    )

    for idx, network_id in enumerate(['MSNBCW', 'CNNW', 'FOXNEWSW']):
        # Ground state data.
        sum_subj_g, n_subj_g = _get_ground(
            subject_counts_df, network_id, partition_infos
        )
        sum_obj_g, n_obj_g = _get_ground(
            object_counts_df, network_id, partition_infos
        )
        # Excited state data.
        sum_subj_e, n_subj_e = _get_excited(
            subject_counts_df, network_id, partition_infos
        )
        sum_obj_e, n_obj_e = _get_excited(
            object_counts_df, network_id, partition_infos
        )
        freq_subj_g = sum_subj_g / n_subj_g
        freq_obj_g = sum_obj_g / n_obj_g
        freq_subj_e = sum_subj_e / n_subj_e
        freq_obj_e = sum_obj_e / n_obj_e

        reactivity_diff_subj = ((freq_subj_e - freq_subj_g) / 2.0)
        reactivity_diff_obj = ((freq_obj_e - freq_obj_g) / 2.0)

        totals_subj = sum_subj_g + sum_subj_e
        totals_obj = sum_obj_g + sum_obj_e

        network = networks[idx]
        for subject in subjects:
            df.loc["Subject=" + subject, network] = [
                freq_subj_g[subject],
                freq_subj_e[subject],
                reactivity_diff_subj[subject],
                totals_subj[subject]
            ]

        for object_ in objects:
            df.loc["Object=" + object_, network] = [
                freq_obj_g[object_],
                freq_obj_e[object_],
                reactivity_diff_obj[object_],
                totals_obj[object_]
            ]

        fancy_columns = ['$f^{(1)}$', '$f^{(2)}$', 'reactivity', 'total uses']
        df.columns = fancy_columns

    return df


def _get_ground(counts_df, network_id, partition_infos,
                words=None, subj_objs=None):
        cdf = counts_df
        net_pi = partition_infos[network_id]
        ground_dates = ((cdf.index < net_pi.partition_date_1.date()) |
                        (cdf.index > net_pi.partition_date_2.date()))

        ret = cdf[ground_dates][network_id].sum()
        n_ground = Counter(ground_dates)[True]

        if words is not None:
            # Only take the indices of interest; these are 1D.
            return ret.loc[words], n_ground
        else:
            return ret, n_ground


def _get_excited(counts_df, network_id, partition_infos,
                 words=None, subj_objs=None):
    cdf = counts_df
    net_pi = partition_infos[network_id]

    excited_dates = ((cdf.index >= net_pi.partition_date_1.date()) &
                     (cdf.index <= net_pi.partition_date_2.date()))

    ret = cdf[excited_dates][network_id].sum()
    n_excited = Counter(excited_dates)[True]
    if words is not None:
        # Only take the indices of interest; these are 1D.
        return ret.loc[words], n_excited
    else:
        return ret, n_excited


def viomet_analysis_setup(year=2012):
    '''
    Returns:
        viomet_df and partition_infos
    '''
    if year == 2012:
        iatv_corpus_name = 'Viomet Sep-Nov 2012'
        metaphors_url = 'http://metacorps.io/static/data/' + \
                        'viomet-2012-snapshot-project-df.csv'
        date_range = pd.date_range('2012-9-1', '2012-11-30', freq='D')
    if year == 2016:
        iatv_corpus_name = 'Viomet Sep-Nov 2016'
        metaphors_url = 'http://metacorps.io/static/data/' + \
                        'viomet-2016-snapshot-project-df.csv'
        date_range = pd.date_range('2016-9-1', '2016-11-30', freq='D')

    viomet_df = get_project_data_frame(metaphors_url)
    fits = fit_all_networks(viomet_df, date_range, iatv_corpus_name)
    networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']
    partition_infos = {network: fits[network][0]
                       for network in networks}

    return viomet_df, date_range, partition_infos


def fit_all_networks(df, date_range, iatv_corpus_name,
                     by_network=True, poisson=False, verbose=False):

    ic = IatvCorpus.objects(name=iatv_corpus_name)[0]

    # The first date of date_range can't be the last excited state date.
    last_excited_date_candidates = date_range[1:]

    candidate_excited_date_pairs = [
        (fd, ld)
        for ld in last_excited_date_candidates
        for fd in date_range[date_range < ld]
    ]

    if by_network:

        if iatv_corpus_name is None:
            raise RuntimeError(
                'If by_network=True, must provide iatv_corpus_name'
            )

        network_freq = daily_frequency(df, date_range, ic, by=['network'])

        results = {}
        for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']:

            single_network = \
                network_freq[network].to_frame().reset_index().dropna()

            # this is ugly but required to match partition_AICs at this time
            single_network.columns = ['date', 'freq']

            all_fits = partition_AICs(single_network,
                                      candidate_excited_date_pairs,
                                      model_formula='freq ~ state',
                                      poisson=poisson,
                                      verbose=verbose)

            # The first date of the second level state cannot be the first
            # date in the dataset.
            all_fits = all_fits[all_fits.first_date != datetime(2012, 9, 1)]

            # The best fit is the one with the minimum AIC.
            best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

            # PartitionInfo provides a data structure wrapper around data row.
            pinfo = PartitionInfo.from_fit(best_fit)

            if poisson:
                pinfo.f_ground /= 2.0
                pinfo.f_excited /= 2.0

            results.update({network: (pinfo, best_fit, all_fits)})

        return results

    else:

        all_freq = daily_frequency(df, date_range, ic).reset_index().dropna()

        all_freq.columns = ['date', 'freq']

        all_fits = partition_AICs(all_freq,
                                  candidate_excited_date_pairs,
                                  model_formula='freq ~ state')

        best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

        return best_fit
