'''
Read in coded contexts from Excel spreadsheet review.xlsx;
create timeseries plots of cumulative counts of each of the key violent words,
which so far are:
    * hit
    * attack
    * knockout
    * punch
    * knock
    * blood
    * struck
    * strike
'''
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from datetime import datetime, date

from util import extract_datetime

plt.style.use('ggplot')


# cut and pasted from
# http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
CUSTOM_COLORS = [
    (31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
    (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
    (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
    (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
    (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)
]

for i in range(len(CUSTOM_COLORS)):
    r, g, b = CUSTOM_COLORS[i]
    CUSTOM_COLORS[i] = (r / 255., g / 255., b / 255.)


#: plot cumulative count figures for total and individual stations
def plot_cumulative(station, fig_counts):

    cumulative_figurative_counts = fig_counts.cumsum()
    ax = cumulative_figurative_counts.plot(
        lw=2, marker='o', color=CUSTOM_COLORS
    )

    ax.set_title(station.upper())
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative counts')

    ax.axvline(date(2012, 10, 3), color='k', lw=1)
    ax.axvline(date(2012, 10, 11), color='k', lw=1)
    ax.axvline(date(2012, 10, 16), color='k', lw=1)
    ax.axvline(date(2012, 10, 22), color='k', lw=1)
    ax.axvline(date(2012, 10, 29), color='k', ls='--', lw=1)

    plt.subplots_adjust(bottom=0.25)


def plot_allfig_ts_bar(station, fig_counts):

    ax = fig_counts.plot(kind='bar', x=fig_counts.index,
                         color=CUSTOM_COLORS, stacked=True)

    # customize tick labels
    ticklabels = ['']*len(fig_counts.index)
    ticklabels[0] = 'October 1, 2012'
    ticklabels[5::5] = [d.strftime('%d') for d in fig_counts.index[5::5]]

    ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))
    plt.gcf().autofmt_xdate()

    ax.set_title(station.upper())
    ax.set_ylabel('Daily counts')
    ax.set_xlabel('Date')

    ax.axvline(2, color='k', lw=1)
    ax.axvline(10, color='k', lw=1)
    ax.axvline(15, color='k', lw=1)
    ax.axvline(21, color='k', lw=1)
    ax.axvline(27, color='k', ls='--', lw=1)

    plt.subplots_adjust(bottom=0.25)


words = [
    w.upper() for w in
    ['hit', 'attack', 'knockout', 'punch', 'knock', 'blood',
     'struck', 'strike', ]
]

rng = pd.date_range(datetime(2012, 10, 1), datetime(2012, 10, 31), freq='D')

daily_figurative_counts = pd.DataFrame(0, index=rng, columns=words)

xl = pd.ExcelFile('review.xlsx')

figurative_counts = {
    station: pd.DataFrame(0, index=rng, columns=words)
    for station in ('cnn', 'fox', 'msnbc')
}

for word in words:

    df = pd.read_excel(xl, word, index_col=None, parse_cols='B,H')

    # extract all figurative and interesting uses
    df_fi = df[df.code == 'fi']

    # need to create indices first in case there are no matches
    # all_instance_dates = extract_datetime(df_fi.filename)
    cnn_row_idxs = ['CNN' in el for el in df_fi.filename]
    fox_row_idxs = ['FOX' in el for el in df_fi.filename]
    msnbc_row_idxs = ['MSNBC' in el for el in df_fi.filename]

    if any(cnn_row_idxs):
        cnn_instance_dates = extract_datetime(df_fi[cnn_row_idxs].filename)
    else:
        cnn_instance_dates = None

    if any(fox_row_idxs):
        fox_instance_dates = extract_datetime(df_fi[fox_row_idxs].filename)
    else:
        fox_instance_dates = None

    if any(msnbc_row_idxs):
        msnbc_instance_dates = extract_datetime(df_fi[msnbc_row_idxs].filename)
    else:
        msnbc_instance_dates = None

    instance_dates = {
        'cnn': cnn_instance_dates,
        'fox': fox_instance_dates,
        'msnbc': msnbc_instance_dates
    }

    for station, dates in instance_dates.items():
        if dates is not None:
            for d in dates:
                figurative_counts[station][word][d.date()] += 1

all_figurative_counts = figurative_counts['cnn'] + \
    figurative_counts['fox'] + \
    figurative_counts['msnbc']

figurative_counts.update(
    {'Total of CNN, MSNBC, and FOX': all_figurative_counts}
)

for station, fig_counts in figurative_counts.items():

    plot_cumulative(station, fig_counts)

    plot_allfig_ts_bar(station, fig_counts)
