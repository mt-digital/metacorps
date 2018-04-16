'''
Testing hypothesis that metaphorical violence usage in 2016 is correlated with
Donald Trump's tweeting.
'''
import json
import pandas as pd

from collections import Counter
from datetime import date
from os.path import join as osjoin

from projects.common import daily_frequency, get_project_data_frame


METAPHORS_URL = \
    'http://metacorps.io/static/data/viomet-2016-snapshot-project-df.csv'
DATE_RANGE = pd.date_range('2016-9-1', '2016-11-30', freq='D')
IATV_CORPUS_NAME = 'Viomet Sep-Nov 2016'


def _local_date(d_str):
    '''
    Checking the raw data against
    http://www.trumptwitterarchive.com/archive/none/ftff/9-1-2016_11-30-2016
    revealed that the raw time is UTC.
    '''
    return pd.to_datetime(
            d_str
        ).tz_localize(
            'UTC'
        ).tz_convert(
            'US/Eastern'
        ).date()


def get_tweets_ts(candidate):

    tweets = json.load(open('data/{}_tweets_2016.json'.format(candidate), 'r'))
    dates = [_local_date(el['created_at']) for el in tweets]
    focal_dates = [d for d in dates
                   if date(2016, 9, 1) <= d
                   and d <= date(2016, 11, 30)]
    date_counts = Counter(focal_dates)
    tweets_ts = pd.Series(index=DATE_RANGE, data=0)
    for d, count in date_counts.items():
        tweets_ts[d] = count

    return tweets_ts


def get_subjobj_ts(**kwargs):
    pass


def correlate(save_dir=None):

    # Create metaphorical violence frequency series across all networks.
    df = get_project_data_frame(METAPHORS_URL)
    freq_df = daily_frequency(df, DATE_RANGE, IATV_CORPUS_NAME)
    metvi_ts = pd.Series(index=freq_df.index, data=freq_df['freq'])
    metvi_ts.fillna(0.0, inplace=True)

    # Create timeseries of Trump tweets.
    ts_data = dict(
        trump=get_tweets_ts('trump'),
        clinton=get_tweets_ts('clinton'),
        metvi_all=metvi_ts,
        # metvi_trump_subj=get_subjobj_ts(subj='trump'),
        # metvi_trump_obj=get_subjobj_ts(obj='trump'),
        # metvi_clinton_subj=get_subjobj_ts(subj='clinton'),
        # metvi_clinton_obj=get_subjobj_ts(obj='clinton')
    )

    if save_dir is not None:

        def mkpath(name):
            return osjoin(save_dir, name + '.csv')

        save_paths = dict(
            trump=mkpath('trump-tweets'),
            clinton=mkpath('clinton-tweets'),
            metvi_all=mkpath('metvi-all'),
            # metvi_trump_subj=mkpath('metvi-trump-subj'),
            # metvi_trump_obj=mkpath('metvi-trump-obj'),
            # metvi_clinton_subj=mkpath('metvi-clinton-subj'),
            # metvi_clinton_obj=mkpath('metvi-clinton-obj')
        )

        for key, path in save_paths.items():
            ts = ts_data[key]
            ts.to_csv(path, header=False)

    return ts_data
