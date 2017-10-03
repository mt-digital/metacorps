import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from collections import OrderedDict, Counter
from datetime import datetime, timedelta

from .export_project import ProjectExporter
from app.models import IatvCorpus

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


def get_analyzer(project_name):
    '''
    Convenience method for creating a newly initialized instance of the
    Analyzer class. Currently the only argument is year since the projects all
    contain a year. In the future we may want to match some other unique
    element of a title, or create some other kind of wrapper to search
    all Project names in the metacorps database.

    Arguments:
        project_name (str): name of project to be exported to an Analyzer
            with DataFrame representation included as an attribute
    '''
    if type(project_name) is int:
        project_name = str('Viomet Sep-Nov ' + project_name)

    return Analyzer(
        ProjectExporter(project_name).export_dataframe()
    )


class Analyzer:
    '''
    Wrapper for various analysis routines. Needs a properly-formatted
    pandas DataFrame to initialize. The `get_analyzer` is the best way to
    get a new Analyzer instance; it handles querying the database and
    formatting the dataframe.
    '''

    def __init__(self, df):
        '''
        Arguments:
            df (pandas.DataFrame): properly-formatted dataframe for generating
                a new Analyzer. See behavior of
                ProjectExporter.export_dataframe for how to format, or just
                use it directly.
        '''
        self.df = df

    def per_network_facet_counts(self,
                                 date_ranges=DEFAULT_DATE_RANGES,
                                 data_method='daily-average'):
        # XXX fix docstring
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
                    _select_range_and_pivot_daily_counts(
                        date_range, counts_df, data_method
                    )
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

    def plot_agency_counts_by_dateranges(self,
                                         subj_obj,
                                         date_ranges=DEFAULT_DATE_RANGES,
                                         pdf_output=False):

        ag = self.agency_counts_by_dateranges(subj_obj)

        if pdf_output:
            pass
        else:
            _plot_agency_counts_by_dateranges(ag, subj_obj, date_ranges)

        plt.tight_layout()

    def network_daily_timeseries(self, facets=None):
        """
        Create a timeseries for every network with each column a facet.

        Arguments: None

        Returns (dict): Dictionary of timeseries as explained in description
        """
        pass

    def subject_counts(self, obj=None):
        '''
        Return daily frequency of subjects of metaphorical violence with
        columns | date | subject | counts |

        Believe this will require a groupby subject, then aggregate over
        day.
        '''
        pass

    def agency_counts_by_dateranges(self,
                                    subj_obj,
                                    date_ranges=DEFAULT_DATE_RANGES):
        """
        Arguments:
            subj_obj (str): either 'subjects' or 'objects'

        Returns (dict): dictionary with keys of date ranges as in the
            per-network facet counts. Values are dataframes with
            indexes networks and columns with clinton-object, clinton-subject,
            trump-object, trump-subject. Of course this needs to be generalized
            for 2012, but leave that as a TODO
        """
        counts_df = _count_daily_subj_obj(self.df, subj_obj)

        ret_dict = {}
        for rng_name, date_range in date_ranges.items():
            ret_dict.update(
                {
                    rng_name:
                    _select_range_and_pivot_subj_obj(
                        date_range, counts_df, subj_obj
                    )
                }
            )

        return ret_dict


def _select_range_and_pivot_subj_obj(date_range, counts_df, subj_obj):

    rng_sub = counts_df[
        date_range[0] <= counts_df.start_localtime
    ][
        counts_df.start_localtime <= date_range[1]
    ]

    rng_sub_sum = rng_sub.groupby(['network', subj_obj]).agg(sum)

    ret = rng_sub_sum.reset_index().pivot(
        index='network', columns=subj_obj, values='counts'
    )

    return ret


def _count_daily_subj_obj(df, sub_obj):

    subs = df[['start_localtime', 'network', 'subjects', 'objects']]

    subs.subjects = subs.subjects.map(lambda s: s.strip().lower())
    subs.objects = subs.objects.map(lambda s: s.strip().lower())

    try:
        trcl = subs[
            (subs[sub_obj].str.contains('hillary clinton') |
             subs[sub_obj].str.contains('donald trump')) &
            subs[sub_obj].str.contains('/').map(lambda b: not b) &
            subs[sub_obj].str.contains('campaign').map(lambda b: not b)
        ]
    except KeyError:
        raise RuntimeError('sub_obj must be "subjects" or "objects"')

    c = trcl.groupby(['start_localtime', 'network', sub_obj]).size()

    ret_df = c.to_frame()
    ret_df.columns = ['counts']
    ret_df.reset_index(inplace=True)

    # cleanup anything like 'republican nominee'
    ret_df.loc[
        :, sub_obj
    ][

        ret_df[sub_obj].str.contains('donald trump')

    ] = 'donald trump'

    ret_df.loc[
        :, sub_obj
    ][

        ret_df[sub_obj].str.contains('hillary clinton')

    ] = 'hillary clinton'

    return ret_df


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


def shows_per_date(date_index, iatv_corpus, by_network=False):
    '''
    Arguments:
        date_index (pandas.DatetimeIndex): Full index of dates covered by
            data
        iatv_corpus (app.models.IatvCorpus): Obtained, e.g., using
            `iatv_corpus = IatvCorpus.objects.get(name='Viomet Sep-Nov 2016')`
        by_network (bool): whether or not to do a faceted daily count
            by network

    Returns:
        (pandas.Series) if by_network is False, (pandas.DataFrame)
            if by_network is true.
    '''
    if type(iatv_corpus) is str:
        iatv_corpus = IatvCorpus.objects(name=iatv_corpus)[0]

    docs = iatv_corpus.documents

    n_dates = len(date_index)

    if not by_network:

        # get all date/show name tuples & remove show re-runs from same date
        prog_dates = set(
            [
                (d.program_name, d.start_localtime.date())
                for d in docs
            ]
        )

        # count total number of shows on each date
        # note we count the second entry of the tuples, which is just the
        # date, excluding program name
        shows_per_date = Counter(el[1] for el in prog_dates)

        spd_series = pd.Series(
            index=date_index,
            data={'counts': np.zeros(n_dates)}
        ).sort_index()

        for date in shows_per_date:
            spd_series.loc[date] = shows_per_date[date]

        return spd_series

    else:
        # get all date/network/show name tuples
        # & remove show re-runs from same date
        prog_dates = set(
            [
                (d.program_name, d.network, d.start_localtime.date())
                for d in docs
            ]
        )

        # count total number of shows on each date for each network
        # note we count the second entry of the tuples, which is just the
        # date, excluding program name
        shows_per_network_per_date = Counter(el[1:] for el in prog_dates)

        n_dates = len(date_index)
        spd_frame = pd.DataFrame(
            index=date_index,
            data={
                'MSNBCW': np.zeros(n_dates),
                'CNNW': np.zeros(n_dates),
                'FOXNEWSW': np.zeros(n_dates)
            }
        )

        for tup in shows_per_network_per_date:
            spd_frame.loc[tup[1]][tup[0]] = shows_per_network_per_date[tup]

        return spd_frame


def daily_metaphor_counts(df, date_index, by=None):
    '''
    Given an Analyzer.df, creates a pivot table with date_index as index. Will
    group by the column names given in by. First deals with hourly data in
    order to build a common index with hourly data, which is the data's
    original format.

    Arguments:
        df (pandas.DataFrame)
        by (list(str))
        date_index (pandas.core.indexes.datetimes.DatetimeIndex): e.g.
            `pd.date_range('2016-09-01', '2016-11-30', freq='D')`
    '''
    # get initial counts by localtime
    if by is None:
        by = []

    counts = _count_by_start_localtime(df, column_list=by)

    # add timedelta to get all hours of the last requested day
    hourly_index = pd.date_range(
        date_index[0], date_index[-1] + timedelta(1, -50), freq='H'
    )

    full_df = pd.DataFrame(index=hourly_index, columns=by + ['counts'],
                           dtype=np.int32)

    # XXX git a good comment in here, wtf is going on
    for r in counts.itertuples():
        full_df.loc[r.start_localtime] = \
            [r.__getattribute__(attr) for attr in by] + [r.counts]

    full_df.counts = full_df.counts.fillna(0)

    piv = pd.pivot_table(full_df, index=full_df.index, values='counts',
                         columns=by, aggfunc=np.sum)

    return piv.fillna(0).resample('D').sum()


def daily_frequency(df, date_index, iatv_corpus, by=None):

    if by is not None and 'network' in by:
        spd = shows_per_date(date_index, iatv_corpus, by_network=True)
        daily = daily_metaphor_counts(df, date_index, by=by)
        ret = daily.div(spd, axis='rows')

    elif by is None:
        spd = shows_per_date(date_index, iatv_corpus)
        daily = daily_metaphor_counts(df, date_index, by=by)
        ret = daily.div(spd, axis='rows')
        ret.columns = ['freq']

    else:
        spd = shows_per_date(date_index, iatv_corpus)
        daily = daily_metaphor_counts(df, date_index, by=by)
        ret = daily.div(spd, axis='rows')

    return ret


class SubjectObjectData:

    def __init__(self, data_frame, subj, obj, partition_infos=None):
        self.data_frame = data_frame
        self.subject = subj
        self.object = obj
        self.partition_infos = partition_infos
        self.partition_data_frame = None

    @classmethod
    def from_analyzer_df(cls, analyzer_df, subj=None, obj=None,
                         subj_contains=True, obj_contains=True,
                         date_range=pd.date_range(
                             '2016-09-01', '2016-11-30', freq='D'
                         )):
        '''
        Given an Analyzer instance's DataFrame, calculate the frequency of
        metaphorical violence with a given subject, object,
        or a subject-object pair.

        Returns:
            (SubjectObjectData) an initialized class. The data_frame attribute
            will be filled with by-network counts of the specified subj/obj
            configuration.
        '''

        pre = analyzer_df

        def _match_checker(df, subj, obj, subj_contains, obj_contains):
            '''
            Returns list of booleans for selecting subject and object matches
            '''

            if subj is None and obj is None:
                raise RuntimeError('subj and obj cannot both be None')

            if subj is not None:
                if subj_contains:
                    retSubj = list(df.subjects.str.contains(subj))
                else:
                    retSubj = list(df.subjects == subj)

                if obj is None:
                    ret = retSubj

            # TODO could probably combine these, but now not clear how
            if obj is not None:
                if obj_contains:
                    retObj = list(df.objects.str.contains(obj))
                else:
                    retObj = list(df.objects == obj)

                if subj is None:
                    ret = retObj
                else:
                    ret = [rs and ro for rs, ro in zip(retSubj, retObj)]

            return ret

        pre = pre[
            _match_checker(pre, subj, obj, subj_contains, obj_contains)
        ]

        # then do counts or frequencies as normal, since you have just
        # subset the relevant rows.
        counts_df = pd.DataFrame(
            index=date_range, data=0.0,
            columns=pd.Index(['MSNBCW', 'CNNW', 'FOXNEWSW'], name='network')
        )
        # there might be columns missing, so we have to insert into above zeros
        to_insert_df = daily_metaphor_counts(pre, date_range, by=['network'])
        # counts_df = daily_metaphor_counts(pre, date_range, by=['network'])[
        #     ['MSNBCW', 'CNNW', 'FOXNEWSW']
        # ]
        # import ipdb
        # ipdb.set_trace()
        for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']:
            if network in to_insert_df.columns:
                for row in to_insert_df.itertuples():
                    counts_df.loc[row.Index][network] = \
                            row.__getattribute__(network)

        # import ipdb
        # ipdb.set_trace()

        return cls(counts_df, subj, obj)

    def partition(self, partition_infos):
        pass
