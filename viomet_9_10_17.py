import pandas as pd
# import matplotlib.pyplot as plt

from datetime import date

from app.models import IatvCorpus
from projects.common.analysis import (
    shows_per_date, daily_counts, get_analyzer
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


def fit_all_networks(analyzer, dr, freq=True, shows_per_date=None):

    if freq:

        if shows_per_date is None:
            raise RuntimeError('If freq=True, must provide shows_per_date')

        dr = pd.date_range('2016-09-01', '2016-11-30', freq='D')

        full_df = daily_counts(
            analyzer.df, ['network'], dr
        )[['MSNBCW', 'CNNW', 'FOXNEWSW']]

        # XXX NOT QUITE RIGHT -- NEED TO DIVIDE BY NUMBER OF SHOWS ON EACH
        # NETWORK!!! BEING FIXED IN projects.common.analysis.shows_per_date
        network_freq = full_df.div(shows_per_date, axis='rows')

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

            # tau1 = best_fit.first_date
            # tau2 = best_fit.second_date

            results.update({network: best_fit})

            print('finished fitting', network)

        return results

    else:
        pass


if __name__ == '__main__':

    generate_figures()
