'''
Plots for my first-year (and beyond) figurative violence in the media project.

Author: Matthew Turner <maturner01@gmail.com>

Date: April 01, 2017
'''
import matplotlib.dates as dates
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import date
from matplotlib import font_manager

from fyr_analysis import relative_likelihood


CUR_PAL = sns.color_palette()


# FIGURE 1
def plot_daily_usage(df, ma_period=7, lw=3, marker='o', ms=10, xlab='Date',
                     ylab='Figurative uses',
                     title='Figurative uses of violent words'):
    '''
    Plot daily and `ma_period`-day moving average from dataframe with index
    of every date in observation period (currently Sep 1 - Nov 30)
    '''
    sns.set(font_scale=1.75)

    # calculate the moving average over ma_period
    ma = df.rolling(ma_period).mean().fillna(0)

    ax = ma.plot(lw=lw, figsize=(15, 12))

    df.plot(marker='o', ms=ms, lw=0, ax=ax, color=CUR_PAL)

    p, _ = ax.get_legend_handles_labels()
    leg = ax.legend(p, ['attack ({}-day MA)'.format(ma_period), 'beat', 'hit',
                        'attack (daily)', 'beat', 'hit'], frameon=True)

    leg.get_frame().set_facecolor('white')

    # XXX magic number gotten from ipython session
    plt.xlim([17044, plt.xlim()[1]])

    plt.ylim([0, 17])

    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.title(title)

    ax.axvline(date(2016, 9, 26), color='k', lw=3, ls='--')
    ax.axvline(date(2016, 10, 9), color='k', lw=3, ls='--')
    ax.axvline(date(2016, 10, 19), color='k', lw=3, ls='--')
    ax.axvline(date(2016, 11, 8), color='k', lw=3, ls='--')

    plt.tight_layout()


def plot_total_daily_usage(series, ma_period=5, lw=3, marker='o', ms=6,
                           xlab='Date', ylab='Frequency of uses',
                           plot_ma=False,
                           show_debates=False, show_election=False,
                           show_means=False,
                           save_path=None,
                           title='Figurative violence usage during debate season'):
    sns.set(font_scale=1.5)

    fig = plt.figure(figsize=(16, 9))
    ax = series.plot(style='ok', markerfacecolor="None", markeredgecolor="black",
                     markeredgewidth=5, lw=0, ms=ms)

    if plot_ma:
        ma = series.rolling(ma_period).mean().fillna(0)

        ax = ma.plot(style='k-', lw=lw, ax=ax, figsize=(15, 12))

        p, _ = ax.get_legend_handles_labels()
        leg = ax.legend(p, ['frequency of usage ({}-day) MA'.format(ma_period),
                            'frequency of usage per day'
                            ]
                        )
    # else:
        # p, _ = ax.get_legend_handles_labels()
        # leg = ax.legend(p, ['frequency of usage per day'])

    # leg.get_frame().set_facecolor('white')

    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.title(title)

    if show_debates:
        ax.axvline(date(2016, 9, 26), color='#cc0000', lw=3, ls='--')
        ax.axvline(date(2016, 10, 9), color='#cc0000', lw=3, ls='--')
        ax.axvline(date(2016, 10, 19), color='#cc0000', lw=3, ls='--')

        plt.text(date(2016, 9, 25), 6, 'First Debate\nSeptember 26',
                 horizontalalignment='right', color='#cc0000')
        plt.text(date(2016, 10, 8), 6.5, 'Second Debate\nOctober 9',
                 horizontalalignment='right', color='#cc0000')
        plt.text(date(2016, 10, 20), 6, 'Third Debate\nOctober 19',
                 horizontalalignment='left', color='#cc0000')
    if show_election:
        ax.axvline(date(2016, 11, 8), color='#cc0000', lw=3, ls='--')

    if show_means:
        ax.plot(
            [date(2016, 9, 1), date(2016, 9, 24)], [1, 1],
            lw=5, color='#cc0000'
        )
        ax.plot(
            [date(2016, 9, 25), date(2016, 10, 26)], [2.7, 2.7],
            lw=5, color='#cc0000'
        )
        ax.plot(
            [date(2016, 10, 27), date(2016, 11, 30)], [1, 1],
            lw=5, color='#cc0000'
        )

    ax.xaxis.set_major_formatter(dates.DateFormatter('%m/%d/%Y'))
    ax.xaxis.set_major_locator(dates.DayLocator(bymonthday=(1, 15)))

    plt.tight_layout()

    if save_path is not None:
        fig.savefig(save_path)
        plt.close()

    return ax


# FIGURE 2
def aic_heatmap(df, relative=False, lw=2, annot=True, lim_ticklabels=False,
                title='', save_path=None):
    '''
    heatmap demonstrating relative likelihood of each model minimizing
    information loss

    Arguements:
        df (pandas.DataFrame): data frame with the first and second
            partition dates and an AIC column if relative=False and a
            rl column if relative=True
        relative (bool): see above

    Returns:
        (matplotlib.pyplot.Axes): Axes plotted to
    '''
    sns.set(font_scale=1.2)

    cbar_kws = dict(label='Relative Likelihood, $\mathcal{L}_i$', size=16)

    fig = plt.figure(figsize=(16, 9))

    if relative:
        val_col = 'rl'
        fmt = '.2f'

        df_rel = df.copy()
        min_aic = df_rel.AIC.min()

        df_rel = df_rel.rename(columns={'AIC': val_col})
        df_rel[val_col] = relative_likelihood(min_aic, df_rel[val_col])

        if lim_ticklabels:
            ax = sns.heatmap(
                df_rel.pivot('first_date', 'second_date', val_col),
                annot=annot, fmt=fmt, linewidths=lw, xticklabels=5,
                yticklabels=5
            )

        else:
            ax = sns.heatmap(
                df_rel.pivot('first_date', 'second_date', val_col),
                annot=annot, fmt=fmt, linewidths=lw
            )

        cbar = plt.gcf().axes[-1]  # .colorbar(df_rel[val_col].values)
        cbar.tick_params(labelsize=14)
        cbar.set_title('Relative Likelihood, $\mathcal{L}_i$\n',
                       size=18, loc='left')

    else:
        fmt = '1.0f'

        if lim_ticklabels:
            ax = sns.heatmap(
                df_rel.pivot('first_date', 'second_date', val_col),
                annot=annot, fmt=fmt, linewidths=lw, xticklabels=5,
                yticklabels=5, cbar_kws=cbar_kws
            )

        else:
            ax = sns.heatmap(
                df_rel.pivot('first_date', 'second_date', val_col),
                annot=annot, fmt=fmt, linewidths=lw, cbar_kws=cbar_kws
            )


    ax.set_ylabel('Date frequency increased', size=20)
    ax.set_xlabel('Date frequency returned to normal', size=20)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, size=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=-30, ha='left', size=15)

    ax.invert_yaxis()
    plt.title(title, size=22)
    plt.tight_layout()

    if save_path is not None:
        fig.savefig(save_path)
        plt.close()

    return ax


# FIGURE 3
def source_framing():
    '''
    hit, attack, and beat pairwise correlation plots for each
    statistically-determined phase
    '''
    pass
