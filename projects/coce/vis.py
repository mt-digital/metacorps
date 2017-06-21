'''
20 June 2017
'''
import matplotlib.dates as dates
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import date
from matplotlib import font_manager

from fyr_analysis import relative_likelihood


CUR_PAL = sns.color_palette()

def plot_three_speakers(speaker_counts_df):

    _plot_one(speaker_counts_df, ['Ted Cruz'])
    _plot_one(speaker_counts_df, ['Ted Cruz', 'Donald Trump'])
    _plot_one(speaker_counts_df, ['Ted Cruz', 'Donald Trump', 'Other'])


def _plot_one(speaker_counts, speakers, stacked=False):
    '''
    Arguments:
        columns (list): names of speakers to include in graph.
    '''
    sns.set(font_scale=1.0)
    sns.set_style('whitegrid')
    sns.set_style('ticks')

    sc = speaker_counts

    ax = sc[speakers].plot(kind='bar', stacked=stacked, figsize=(8, 4.5),
                           legend=False)

    ax.set_xticklabels(sc.index.strftime('%b %Y'), rotation=45, ha='right')

    ax.xaxis.grid(False)
    ax.yaxis.grid(True)

    ax.set_ylim(0, 26)

    ax.set_xlabel('Month')
    ax.set_ylabel('Number of instances')

    plt.legend(loc='best', frameon=True)

    sns.despine()

    plt.tight_layout()

    plt.savefig('-'.join(speakers).replace(' ', '') + '.png', dpi=300)

    return ax
