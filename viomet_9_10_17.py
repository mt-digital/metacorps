import numpy as np
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as pltdates

from datetime import datetime, timedelta
from matplotlib import gridspec

from app.models import IatvCorpus
from projects.common.analysis import (
    shows_per_date, get_project_data_frame,
    daily_metaphor_counts, daily_frequency, facet_word_count,
    SubjectObjectData
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
)

FACET_WORDS = ['attack', 'beat', 'hit', 'slap', 'knock', 'grenade',
               'jugular', 'slug', 'smack', 'strangle']

def generate_figures():

    analyzer = get_project_data_frame('Viomet Sep-Nov 2016')

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


def by_network_frequency_figure(frequency_df,
                                date_range=pd.date_range(
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

    df = frequency_df

    # fits are not being shown for this condition
    if (partition_infos is None):

        if freq:

            network_freq = daily_frequency(
                df, date_range, iatv_corpus_name, by=['network']
            )

            network_freq.plot(style='o')

        else:

            full_df = daily_metaphor_counts(
                df, ['network'], date_range
            )[['MSNBCW', 'CNNW', 'FOXNEWSW']]

            full_df.plot(style='o')

    # show fits TODO Include more arguments so that fits don't have to be
    # generated just to plot. Generate fits outside and pass fits in.
    else:

        if freq:

            # put networks in desired order, left to right
            networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']

            network_freq = daily_frequency(
                df, date_range, iatv_corpus_name, by=['network']
            )

            ax = network_freq[networks].plot(
                style='o', ms=14, alpha=0.5, legend=False, figsize=DEFAULT_FIGSIZE
            )

            for net_idx, network in enumerate(networks):

                pinfo = partition_infos[network]

                day_td = timedelta(seconds=60)

                d0 = date_range[0]
                d1 = pinfo.partition_date_1 - day_td

                d2 = pinfo.partition_date_1
                d3 = pinfo.partition_date_2

                d4 = pinfo.partition_date_2 + day_td
                d5 = date_range[-1]

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
def fit_all_networks(df, date_range, iatv_corpus_name, by_network=True):

    ic = IatvCorpus.objects(name=iatv_corpus_name)[0]

    if by_network:

        if iatv_corpus_name is None:
            raise RuntimeError(
                'If by_network=True, must provide iatv_corpus_name'
            )

        network_freq = daily_frequency(df, date_range, ic, by=['network'])

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

        all_freq = daily_frequency(df, date_range, ic).reset_index().dropna()

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


def _get_excited_chooser(df, partition_infos):
    '''
    Boolean row selection indexer from project data frame obtained using
    get_project_data_frame from projects.common
    '''

    msnbc_pi = partition_infos['MSNBCW']
    msnbc_excited_chooser = (df.network == 'MSNBCW') & \
        (
            (df.start_localtime >= msnbc_pi.partition_date_1) &
            (df.start_localtime <= msnbc_pi.partition_date_2)
        )

    cnn_pi = partition_infos['CNNW']
    cnn_excited_chooser = (df.network == 'CNNW') & \
        (
            (df.start_localtime >= cnn_pi.partition_date_1) &
            (df.start_localtime <= cnn_pi.partition_date_2)
        )

    fox_pi = partition_infos['FOXNEWSW']
    fox_excited_chooser = (df.network == 'FOXNEWSW') & \
        (
            (df.start_localtime >= fox_pi.partition_date_1) &
            (df.start_localtime <= fox_pi.partition_date_2)
        )

    excited_chooser = \
        fox_excited_chooser | msnbc_excited_chooser | cnn_excited_chooser

    return excited_chooser


def by_facet_word(df, partition_infos, facet_words=FACET_WORDS,
                  font_scale=1.15, plot=False, save_path=None):
    '''
    Arguments:
        df (pandas.DataFrame): dataframe of annotations of metaphorical
            violence generated using IatvCorpus data; previously Analyzer.df
        partition_infos (dict): dictionary of
            projects.viomet.analysis.PartitionInfo instances, keyed by the
            network they represent e.g. 'FOXNEWSW'

    Returns:
        None
    '''
    sns.axes_style("darkgrid")
    sns.set(font_scale=font_scale)
    # create choosers to select only excited or ground rows from df

    excited_chooser = _get_excited_chooser(df, partition_infos)

    excited_df = df[excited_chooser]
    ground_df = df[~excited_chooser]

    days_excited = {
        k:
            (partition_infos[k].partition_date_2 -
             partition_infos[k].partition_date_1).days + 1

        for k in ['MSNBCW', 'CNNW', 'FOXNEWSW']
    }

    # XXX
    total_days = 91

    days_ground = {
        k: total_days - v
        for k, v in days_excited.items()
    }

    for k in days_excited:

        fwc_excited = \
            facet_word_count(excited_df, facet_words) / days_excited[k]

        fwc_ground = \
            facet_word_count(ground_df, facet_words) / days_ground[k]

    if plot:
        # make two-panel to start: ground and excited; add a third excited - ground
        # once the two-panel is done.
        gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])
        fig, axes = plt.subplots(nrows=1, ncols=3, sharey=True, figsize=(6, 5))

        # fig.suptitle('Comparison of violent word in ground and excited states')

        p1 = fwc_ground.plot(
            kind='barh', ax=axes[0], title='Ground State', legend=False
        )
        p2 = fwc_excited.plot(
            kind='barh', ax=axes[1], title='Excited State'
        ).legend(loc='lower center', labels=['MSNBC', 'CNN', 'Fox News'],
                bbox_to_anchor=(-0.05, -0.1), ncol=3,
                title='Average daily instances for network')

        p3 = (fwc_excited - fwc_ground).plot(
            kind='barh', ax=axes[2], title='Ground-to-excited change', legend=False
        )

        xlim = (-0.25, 3.75)
        for ax in axes:
            # ax.set_xlabel('Average daily instances')
            ax.set_xticks(np.arange(-0.5, 3.75, 0.5))
            ax.set_xlim(xlim)
            ax.set_xticklabels(
                ['', '0', '', '1', '', '2', '', '3', '']
            )

            ax.set_ylabel('Violent word used in metaphor')

        # legend = fig.legend(loc='upper center',
        #                     labels=['MSNBC', 'CNN', 'Fox News'],
        #                     bbox_to_anchor=(-0.05, -0.065), ncol=3,
        #                     title='Average daily instances for network')

        # plt.tight_layout()
        fig.subplots_adjust(bottom=-0.5)

        if save_path is not None:
            fig.savefig(save_path,
                        bbox_extra_artists=(legend,), bbox_inches='tight')
            plt.close()

    return fwc_excited, fwc_ground


def subject_object_analysis(df,
                            subj_obj=[
                                ('Donald Trump', None),
                                ('Hillary Clinton', None),
                                ('Donald Trump', 'Hillary Clinton'),
                                ('Hillary Clinton', 'Donald Trump'),
                                (None, 'Donald Trump'),
                                (None, 'Hillary Clinton')
                            ],
                            resample_window='1W', font_scale=1.15, plot=False,
                            save_dir='./'):

    # XXX First thing to be done is the weekly timeseries; do this sort of
    # XXX selection and aggregation after full-length subj/obj dfs are made
    # excited_chooser = _get_excited_chooser(df, partition_infos)

    # excited_df = df[excited_chooser]
    # ground_df = df[~excited_chooser]

    # d = dict([
    #     (subj_obj[0],
    #      SubjectObjectData.from_analyzer_df(
    #          df, subj=subj_obj[0][0], obj=subj_obj[0][1]
    #      )
    #      )
    # ])
    sns.set(font_scale=font_scale)
    d = dict([

        (so,

         SubjectObjectData.from_analyzer_df(
                 df, subj=so[0], obj=so[1]
             ).data_frame.fillna(
                 0.0
             ).resample(resample_window).sum()
         )

        for so in subj_obj
    ])

    if plot:

        ylims = [(-0.2, 25), (-0.2, 25), (-0.2, 12), (-0.2, 12),
                 (-0.2, 15), (-0.2, 15)]

        for idx, so_pair in enumerate(subj_obj):

            subject = so_pair[0] if so_pair[0] is not None else 'All'
            object_ = so_pair[1] if so_pair[1] is not None else 'All'

            df = d[so_pair]
            df.columns = ['MSNBC', 'CNN', 'Fox News']
            _plot_subj_obj(subject, object_, df,
                           ylim=ylims[idx], ax=None, save_dir=save_dir)

    return d  # , fig


def _plot_subj_obj(subj, obj, df, legend=True,
                   save_dir='/Users/mt/Desktop/', ylim=(-0.2, 25), ax=None):

    if ax is None:
        df.plot(legend=legend, figsize=(7.5, 5), marker='s', lw=3, ms=8)

        plt.title('Subject: {}, Object: {}'.format(subj, obj))
        plt.ylabel('Weekly counts')
        plt.ylim(ylim)

        file_name = (subj + '-' + obj).replace(' ', '-')
        plt.savefig(
            os.path.join(save_dir, '{}.pdf'.format(file_name))
        )

    else:
        df.plot(ax=ax, legend=legend)
        ax.set_title('Subject: {}, Object: {}'.format(subj, obj))
        ax.set_ylabel('Weekly counts')

        ax.set_ylim(ylim)

if __name__ == '__main__':

    networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']

    # make fits
    icname = 'Viomet Sep-Nov 2016'
    a = get_project_data_frame(icname)
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
