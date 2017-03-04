import matplotlib.pyplot as plt
import seaborn as sns

from collections import OrderedDict
from datetime import datetime

from export_project_csv import ProjectExporter

dt = datetime

DEFAULT_DATE_RANGES = OrderedDict([
    ('Pre-Debates (September 1 - September 26 6:00 PM)',
        (dt(2016, 9, 1), dt(2016, 9, 26, 6,))),
    ('Between First and Second Debates (September 26 7:30 PM - October 9 6:00 PM)',
        (dt(2016, 9, 26, 7, 30), dt(2016, 10, 9, 6))),
    ('Between Second and Third Debates (October 9 7:30 PM - October 19 6:00 PM)',
        (dt(2016, 10, 9, 7, 30), dt(2016, 10, 19, 6))),
    ('Between Third Debate and Election (October 19 7:30 PM - November 8 11:59 PM)',
        (dt(2016, 10, 19, 7, 30), dt(2016, 11, 8, 11, 59, 59))),
    ('Election to End of November (November 9 12:00 AM - November 30)',
        (dt(2016, 11, 9), dt(2016, 11, 30, 11, 59, 59)))
])


COLUMNS_IN_ORDER = [
    'attack',
    'hit',
    'beat',
    'grenade',
    'slap',
    'knock',
    'jugular',
    'smack',
    'strangle',
    'slug',
]

sns.set(style="white", context="talk")
sns.set_palette(sns.color_palette("Set3", 10))


def get_analyzer(year):
    '''

    '''
    if type(year) is int:
        year = str(year)

    return Analyzer(
        ProjectExporter('Viomet Sep-Nov ' + year).export_dataframe()
    )


class Analyzer:

    def __init__(self, df):
        self.df = df

    def per_network_facet_counts(self,
                                 date_ranges=DEFAULT_DATE_RANGES,
                                 data_method='daily-average'):
        """
        Arguments:
            date_ranges (dict): lookup table of date ranges and their names
        Returns:
            (dict) if distribution, dataframe of density of violence
                words for each date range given in date_ranges. If distribution
                is False, returns non-normalized values.
        """
        counts_df = _count_daily_instances(self.df)

        ret_dict = {}
        for rng_name, date_range in date_ranges.items():
            ret_dict.update(
                {
                    rng_name:
                    _select_range_and_pivot(date_range, counts_df, data_method)
                }
            )

        # we want each underlying dataframe to have the same columns for plots
        _standardize_columns(ret_dict)

        return ret_dict

    def plot_facets_by_dateranges(self,
                                  date_ranges=DEFAULT_DATE_RANGES,
                                  data_method='daily-average',
                                  pdf_output=False):

        nfc = self.per_network_facet_counts(date_ranges, data_method)

        if pdf_output:
            _pdf_plot_facets_by_dateranges(nfc, date_ranges, data_method)
        else:
            _plot_facets_by_dateranges(nfc, date_ranges, data_method)

        plt.tight_layout(w_pad=0.5, h_pad=-0.5)

    def agency_counts(df):
        pass


def _standardize_columns(df_dict):

    cols = set()
    for df in df_dict.values():
        cols.update(df.columns)

    for idx, df in enumerate(df_dict.values()):
        for c in cols:
            if c not in df.columns:
                df[c] = 0.0

    # for some reason can't do this in loop above and must use key
    for k in df_dict:
        df_dict[k] = df_dict[k][COLUMNS_IN_ORDER]


def _pdf_plot_facets_by_dateranges(nfc, date_ranges, data_method):
    pass


def _plot_facets_by_dateranges(nfc, date_ranges, data_method):

    max_y = 0.0
    for df in nfc.values():
        max_y = max(max_y, df.max().max())

    fig, axes = plt.subplots(
        figsize=(7, 9.5), ncols=1, nrows=len(list(nfc.keys()))
    )

    for i, k in enumerate(date_ranges.keys()):
        nfc[k].plot(kind='bar', ax=axes[i], rot=0., legend=False)
        # sns.barplot(data=nfc[k], ax=axes[i])
        axes[i].set_title(k)
        axes[i].set_ylim([0.0, max_y + 0.25])

        if data_method == 'distribution':
            axes[i].set_ylabel('relative usage')
        elif data_method == 'daily-average':
            axes[i].set_ylabel('Average Daily Usage')

        axes[i].set_xlabel('')
        axes[i].yaxis.grid()

    legend = axes[0].legend(
            loc='upper center', borderaxespad=0., ncol=5, prop={'size': 12},
            frameon=True
    )

    sns.despine(left=True)

    legend.get_frame().set_facecolor('0.95')
    legend.get_frame().set_linewidth(1.5)


def _count_daily_instances(df):
    """

    """
    subs = df[['start_localtime', 'network', 'facet_word']]

    c = subs.groupby(['start_localtime', 'network', 'facet_word']).size()

    ret_df = c.to_frame()
    ret_df.columns = ['counts']
    ret_df.reset_index(inplace=True)

    return ret_df


def _select_range_and_pivot(date_range, df, data_method):

    # subset only dates in given date range; earlier date assumed first
    rng_sub = df[
        date_range[0] <= df.start_localtime
    ][
        df.start_localtime <= date_range[1]
    ][
        ['network', 'facet_word', 'counts']
    ]

    rng_sub_sum = rng_sub.groupby(['network', 'facet_word']).agg(sum)

    # create pivot table so we can barplot color coded by facet word
    ret = rng_sub_sum.reset_index().pivot(
        index='network', columns='facet_word', values='counts'
    )

    ret.fillna(0.0, inplace=True)

    # normalize the counts if desired
    if data_method == 'distribution':
        for i in range(len(ret)):
            ret.ix[i] = ret.ix[i] / sum(ret.ix[i])
    # make daily average if desired
    elif data_method == 'daily-average':
        days_list = [
            (el[1] - el[0]).days for el in DEFAULT_DATE_RANGES.values()
        ]
        for i in range(len(ret)):
            ret.ix[i] = ret.ix[i] / float(days_list[i])

    return ret
