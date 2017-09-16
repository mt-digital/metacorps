import pandas as pd
# import matplotlib.pyplot as plt

from datetime import date

from app.models import IatvCorpus
from projects.common.analysis import (
    shows_per_date, get_analyzer, daily_frequency
)
from projects.viomet.analysis import partition_AICs


def generate_figures():

    analyzer = get_analyzer('Viomet Sep-Nov 2016')

    spd = shows_per_date(IatvCorpus.objects.get(name='Viomet Sep-Nov 2016'))

    by_network_frequency_figure(analyzer, spd)

    by_network_total_figure(analyzer)


def by_network_total_figure(analyzer,
                            partition_date1=None,
                            partition_date2=None):
    adf = analyzer.df

    if (partition_date1 is None or partition_date2 is None):

        dr = pd.date_range('2016-09-01', '2016-11-30', freq='D')
        full_df = daily_counts(adf, ['network'], dr)

        full_df.sum().plot(kind='bar')

    else:
        return None


def by_network_frequency_figure(analyzer,
                                spd,
                                freq=True,
                                partition_date1=None,
                                partition_date2=None):

    adf = analyzer.df

    if (partition_date1 is None or partition_date2 is None):

        dr = pd.date_range('2016-09-01', '2016-11-30', freq='D')

        full_df = daily_counts(
            adf, ['network'], dr
        )[['MSNBCW', 'CNNW', 'FOXNEWSW']]

        if freq:
            network_freq = full_df.div(spd, axis='rows')

            network_freq.plot(style='o')
        else:
            full_df.plot(style='o')

    else:
        return None


def fit_all_networks(analyzer, dr, freq=True, iatv_corpus_name=None):

    ic = IatvCorpus.objects(name=iatv_corpus_name)[0]

    if freq:

        if iatv_corpus_name is None:
            raise RuntimeError('If freq=True, must provide iatv_corpus_name')

        # dr = pd.date_range('2016-09-01', '2016-11-30', freq='D')

        # full_df = daily_counts(
        #     analyzer.df, ['network'], dr
        # )[['MSNBCW', 'CNNW', 'FOXNEWSW']]

        network_freq = daily_frequency(analyzer.df, dr, ic, by=['network'])

        results = {}
        for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']:

            # fit the model to find \tau^*_1, \tau^*_2, and \phi
            single_network = \
                network_freq[network].to_frame().reset_index().dropna()

            # this is ugly but required to match partition_AICs at this time
            single_network.columns = ['date', 'freq']

            all_fits = partition_AICs(single_network,
                                      model_formula='freq ~ state')

            best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

            results.update({network: best_fit})

            print('finished fitting', network)

        return results

    else:

        all_freq = daily_frequency(analyzer.df, dr, ic).reset_index().dropna()

        all_freq.columns = ['date', 'freq']

        all_fits = partition_AICs(all_freq, model_formula='freq ~ state')

        best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

        return best_fit


if __name__ == '__main__':

    generate_figures()
