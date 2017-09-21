import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as pltdates

from datetime import datetime, timedelta
from matplotlib import gridspec

from app.models import IatvCorpus
from projects.common.analysis import (
    shows_per_date, get_analyzer, daily_metaphor_counts, daily_frequency
)
from projects.viomet.analysis import partition_AICs, PartitionInfo


sns.set()

# for 8.5x11 paper
DEFAULT_FIGSIZE = (7.5, 5)

# in 0 - 6 order used by Python; see
# https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DatetimeIndex.dayofweek.html
WEEKDAYS = (
    'M', 'T', 'W', 'Th',
    'F', 'Sa', 'Su'
    # 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
    # 'Friday', 'Saturday', 'Sunday'
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
        full_df = daily_metaphor_counts(adf, ['network'], dr)

        full_df.sum().plot(kind='bar')

    else:
        return None


DEFAULT_PARTITION_DATES = (datetime(2016, 10, 1), datetime(2016, 10, 31))


def by_network_frequency_figure(analyzer,
                                dr=pd.date_range(
                                    '2016-09-01', '2016-11-30', freq='D'
                                ),
                                iatv_corpus_name=None,
                                freq=True,
                                partition_infos=None,
                                font_scale=1.15,
                                save_path=None):

    sns.axes_style("darkgrid")
    sns.set(font_scale=font_scale)

    CUR_PAL = sns.color_palette()

    adf = analyzer.df

    # fits are not being shown for this condition
    if (partition_infos is None):

        if freq:

            network_freq = daily_frequency(
                adf, dr, iatv_corpus_name, by=['network']
            )

            network_freq.plot(style='o')

        else:

            full_df = daily_metaphor_counts(
                adf, ['network'], dr
            )[['MSNBCW', 'CNNW', 'FOXNEWSW']]

            full_df.plot(style='o')

    # show fits TODO Include more arguments so that fits don't have to be
    # generated just to plot. Generate fits outside and pass fits in.
    else:

        if freq:

            # put networks in desired order, left to right
            networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']

            network_freq = daily_frequency(
                adf, dr, iatv_corpus_name, by=['network']
            )

            ax = network_freq[networks].plot(
                style='o', ms=14, alpha=0.5, legend=False, figsize=DEFAULT_FIGSIZE
            )

            for net_idx, network in enumerate(networks):

                pinfo = partition_infos[network]

                day_td = timedelta(seconds=3600)

                d0 = dr[0]
                d1 = pinfo.partition_date_1 - day_td

                d2 = pinfo.partition_date_1
                d3 = pinfo.partition_date_2

                d4 = pinfo.partition_date_2 + day_td
                d5 = dr[-1]

                fg = pinfo.f_ground
                fe = pinfo.f_excited

                dates = pd.DatetimeIndex([d0, d1, d2, d3, d4, d5])
                datas = [fg, fg, fe, fe, fg, fg]

                network_formatted = ['MSNBC', 'CNN', 'Fox News']
                pd.Series(
                    index=dates, data=datas
                ).plot(
                    lw=8, ax=ax, ls='-', color=CUR_PAL[net_idx], alpha=0.9,
                    legend=True, label=network_formatted[net_idx]
                )

            # ax.xaxis.set_major_formatter(
            #     pltdates.DateFormatter('%B 2016')
            # )
            # ax.xaxis.set_major_locator(
            #     pltdates.MonthLocator()
            # )
            # plt.minorticks_off()
            ax.xaxis.set_minor_formatter(pltdates.DateFormatter('%-d'))
            ax.xaxis.set_minor_locator(pltdates.DayLocator(bymonthday=(1, 15)))

            ax.grid(which='minor', axis='x')

            ax.set_xlabel('Date')
            ax.set_ylabel('Frequency of usage')
            ax.set_title(
                'Metaphorical violence usage on each of the three networks'
            )

            plt.tight_layout()

            if save_path is not None:
                fig = ax.get_figure()
                fig.savefig(save_path)
                plt.close()


# TODO iatv_corpus_name should be something associated with an Analyzer
def fit_all_networks(analyzer, dr, iatv_corpus_name, by_network=True):

    ic = IatvCorpus.objects(name=iatv_corpus_name)[0]

    if by_network:

        if iatv_corpus_name is None:
            raise RuntimeError(
                'If by_network=True, must provide iatv_corpus_name'
            )

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

            pinfo = PartitionInfo.from_fit(best_fit)

            results.update({network: (pinfo, best_fit)})

        return results

    else:

        all_freq = daily_frequency(analyzer.df, dr, ic).reset_index().dropna()

        all_freq.columns = ['date', 'freq']

        all_fits = partition_AICs(all_freq, model_formula='freq ~ state')

        best_fit = all_fits.iloc[all_fits['AIC'].idxmin()]

        return best_fit


def by_weekday_figure(analyzer, date_index, iatv_corpus_name,
                      font_scale=0.65, save_path=None):
    '''
    average frequency and average number per day with errorbars calculated
    from taking std() of the series of All.
    '''
    sns.axes_style("darkgrid")
    sns.set(font_scale=font_scale)

    CUR_PAL = sns.color_palette()

    df = analyzer.df
    counts = daily_metaphor_counts(df, date_index, by=['network'])
    freq = daily_frequency(df, date_index, iatv_corpus_name, by=['network'])

    fig = plt.figure(figsize=DEFAULT_FIGSIZE)
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])

    for i, df in enumerate([counts, freq]):

        # keep df pristine
        df_mean_pre = df.copy()
        df_mean_pre['weekday'] = df.index.dayofweek
        df_mean = df_mean_pre.groupby(['weekday']).mean()

        # now calculate standard deviation of all-networks sum for stacked bars
        # df_std_pre = df.sum(axis=1).to_frame()
        df_std_pre = df.copy()
        df_std_pre['weekday'] = df_std_pre.index.dayofweek
        df_std = df_std_pre.groupby(['weekday']).std()
        # XXX can't quite get error bars to work how I want... oh well

        ax = plt.subplot(gs[i])

        df_mean.index = WEEKDAYS

        rev_idx = list(df_mean.index)
        rev_idx.reverse()

        # import ipdb
        # ipdb.set_trace()

        # xerr = list(df_std[0]/2.0)
        # xerr.reverse()
        # xerr = df_std

        df_mean.loc[rev_idx[2:]][
            ['MSNBCW', 'CNNW', 'FOXNEWSW']
        ].plot(ax=ax, kind='barh', stacked=True,
               # legend=(False, True)[i], xerr=xerr)
               align='center', legend=False)

        # ax.set_xlabel(('average counts', 'average frequency')[i])
        ax.set_title(
            ('Average counts per weekday',
             'Average frequency per weekday')[i]
        )

        if i == 1:
            ax.set_xticks(range(7))
            ax.set_xlim(0, 6.35)
        else:
            ax.set_xticks(range(0, 11, 2))

    # fig.subplots_adjust(bottom=-1.50)
    legend = plt.legend(loc='upper center',
                        labels=['MSNBC', 'CNN', 'Fox News'],
                        bbox_to_anchor=(-0.05, -0.065), ncol=3)

    plt.tight_layout()
    if save_path is not None:
        plt.savefig(save_path)



if __name__ == '__main__':

    networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']

    # make fits
    icname = 'Viomet Sep-Nov 2016'
    a = get_analyzer(icname)
    dr = pd.date_range('2016-09-01', '2016-11-30', freq='D')

    fitall = fit_all_networks(a, dr, icname)

    pis = {network: fitall[network][0] for network in networks}

    # plot fits to pdf
    by_network_frequency_figure(
        a, dr, icname, partition_infos=pis,
        save_path='/Users/mt/workspace/papers/viomet/Figures/dynamic_model_3network.pdf'
    )

    by_weekday_figure(
        a, dr, icname, partition_infos=pis,
        save_path='/Users/mt/workspace/papers/viomet/Figures/by_weekday.pdf'
    )
