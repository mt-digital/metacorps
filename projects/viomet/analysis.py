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


def partition_info_table(viomet_df,
                         date_range,
                         partition_infos):
    '''
    TODO
    '''
    index_keys = [('MSNBC', 'MSNBCW'),
                  ('CNN', 'CNNW'),
                  ('Fox News', 'FOXNEWSW')]

    columns = ['$T_1e$', '$T_Ne$', '$f^g$', '$f^e$', '\% change', 'total uses']

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
            100 * ((pi.f_excited - pi.f_ground) / pi.f_ground),
            counts_df[key].sum()
        ])

    index = [ik[0] for ik in index_keys]

    return pd.DataFrame(data=data, index=index, columns=columns)


def by_network_subj_obj_table(viomet_df,
                              date_range,
                              partition_infos,
                              subjects=['Barack Obama', 'Mitt Romney'],
                              objects=['Barack Obama', 'Mitt Romney']):
    '''
    TODO
    '''
    networks = ['MSNBC', 'CNN', 'Fox News']
    columns = ['fg', 'fe', '\% change', 'total uses']

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

        pct_diff_subj = 100.0 * ((freq_subj_e - freq_subj_g) / 2.0)
        pct_diff_obj = 100.0 * ((freq_obj_e - freq_obj_g) / 2.0)

        totals = sum_subj_g + sum_obj_g + sum_subj_e + sum_obj_e

        network = networks[idx]
        for subject in subjects:
            df.loc["Subject=" + subject, network] = [
                freq_subj_g[subject],
                freq_subj_e[subject],
                pct_diff_subj[subject],
                totals[subject]
            ]

        for object_ in objects:
            df.loc["Object=" + object_, network] = [
                freq_obj_g[object_],
                freq_obj_e[object_],
                pct_diff_obj[object_],
                totals[object_]
            ]

        fancy_columns = ['$f^g$', '$f^e$', '\% change', 'total uses']
        df.columns = fancy_columns

    return df


def by_network_word_table(viomet_df,
                          date_range,
                          partition_infos,
                          words=['hit', 'beat', 'attack']
                          ):
    '''
    Second table in paper
    '''
    networks = ['MSNBC', 'CNN', 'Fox News']
    columns = ['fg', 'fe', 'pct_change', 'total uses']

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

        pct_diff = 100.0 * ((freq_e - freq_g) / 2.0)

        totals = sum_g + sum_e

        network = networks[idx]
        for word in words:
            df.loc[word, network] = [
                freq_g[word], freq_e[word], pct_diff[word], totals[word]
            ]

    fancy_columns = ['$f^g$', '$f^e$', '\% change', 'total uses']
    df.columns = fancy_columns

    return df


def _get_ground(counts_df, network_id, partition_infos,
                words=None, subj_objs=None):
        cdf = counts_df
        net_pi = partition_infos[network_id]
        ground_dates = ((cdf.index < net_pi.partition_date_1) |
                        (cdf.index > net_pi.partition_date_2))

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

    excited_dates = ((cdf.index >= net_pi.partition_date_1) &
                     (cdf.index <= net_pi.partition_date_2))

    ret = cdf[excited_dates][network_id].sum()
    n_excited = Counter(excited_dates)[True]
    if words is not None:
        # Only take the indices of interest; these are 1D.
        return ret.loc[words], n_excited
    else:
        return ret, n_excited


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

    # candidate start & final dates of excited state
    split = len(date_range) // 2
    candidate_start_dates = date_range[15:split]
    candidate_final_dates = date_range[split+1:-15]

    if by_network:

        if iatv_corpus_name is None:
            raise RuntimeError(
                'If by_network=True, must provide iatv_corpus_name'
            )

        network_freq = daily_frequency(df, date_range, ic, by=['network'])

        results = {}
        for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']:

            # fit the model to find \tau^*_1, \tau^*_2, and \phi
            single_network = \
                network_freq[network].to_frame().reset_index().dropna()

            # this is ugly but required to match partition_AICs at this time
            single_network.columns = ['date', 'freq']

            all_fits = partition_AICs(single_network,
                                      first_dates=candidate_start_dates,
                                      second_dates=candidate_final_dates,
                                      model_formula='freq ~ state',
                                      poisson=poisson,
                                      verbose=verbose)

            best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

            pinfo = PartitionInfo.from_fit(best_fit)

            if poisson:
                pinfo.f_ground /= 2.0
                pinfo.f_excited /= 2.0

            results.update({network: (pinfo, best_fit)})

        return results

    else:

        all_freq = daily_frequency(df, date_range, ic).reset_index().dropna()

        all_freq.columns = ['date', 'freq']

        all_fits = partition_AICs(all_freq,
                                  first_dates=candidate_start_dates,
                                  second_dates=candidate_final_dates,
                                  model_formula='freq ~ state')

        best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

        return best_fit
