import pandas as pd
import matplotlib.pyplot as plt

from app.models import IatvCorpus
from projects.common.analysis import (
    shows_per_date, daily_counts, get_analyzer
)


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
        plt.savefig('test-total.pdf')
        plt.show()

    else:
        return None


def by_network_frequency_figure(analyzer,
                                spd,
                                partition_date1=None,
                                partition_date2=None):

    adf = analyzer.df

    if not (partition_date1 is None or partition_date2 is None):

        dr = pd.date_range('2016-09-01', '2016-11-30', freq='D')
        full_df = daily_counts(adf, ['network'], dr)

        network_freq = full_df.div(spd, axis='rows')

        network_freq.plot(style='o')

    else:
        return None


if __name__ == '__main__':

    generate_figures()
