'''
Plots for my first-year (and beyond) figurative violence in the media project.

Author: Matthew Turner <maturner01@gmail.com>

Date: April 01, 2017
'''
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import date

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


# FIGURE 2
def aic_heatmap(df, relative=False, lw=2, annot=True):
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
    sns.set(font_scale=1.0)

    if relative:
        title = 'Relative likelihood of models with different partition dates'
        val_col = 'rl'
        fmt = '.2f'

        df_rel = df.copy()
        min_aic = df_rel.AIC.min()

        df_rel = df_rel.rename(columns={'AIC': val_col})
        df_rel[val_col] = relative_likelihood(min_aic, df_rel[val_col])

        ax = sns.heatmap(
            df_rel.pivot('first_date', 'second_date', val_col),
            annot=annot, fmt=fmt, linewidths=lw
        )

    else:
        title = 'AIC of models with different partition dates'
        fmt = '1.0f'

        ax = sns.heatmap(
            df.pivot('first_date', 'second_date', 'AIC'),
            annot=annot, fmt=fmt, linewidths=lw
        )

    ax.set_ylabel('First partition date', size=18)
    ax.set_xlabel('Second partition date', size=18)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, size=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=-30, ha='left', size=15)

    plt.title(title, size=22)

    return ax


# FIGURE 3
def source_framing():
    '''
    hit, attack, and beat pairwise correlation plots for each
    statistically-determined phase
    '''
    pass
