'''
Script to build network model fits figure and the three tables from our
publication on metaphorical violence on cable news.

Author: Matthew A. Turner
Date: 2018-01-24
'''
import pickle
import os

import pandas as pd

from projects.common import get_project_data_frame
from projects.viomet.analysis import (
    by_network_subj_obj_table, by_network_word_table,
    fit_all_networks, partition_info_table, model_fits_table
)
from projects.viomet.vis import by_network_frequency_figure

YEARS = [2012, 2016]

FORMATTERS = {
    '$f^g$': '{:,.2f}'.format,
    '$f^e$': '{:,.2f}'.format,
    'totals': lambda n: '{:, d}'.format(int(n)),
    '\% change': '{:,.1f}'.format
}

for year in YEARS:

    print('creating tables for {}'.format(year))

    # Build URL for csv of metaphor annotations.
    metaphors_url = \
        'http://metacorps.io/static/data/' \
        'viomet-{}-snapshot-project-df.csv'.format(year)

    # Still need to access the corpus on MongoDB to calculate some frequencies.
    iatv_corpus_name = 'Viomet Sep-Nov {}'.format(year)

    # Load csv into pandas DataFrame and set up the date range for given year.
    viomet_df = get_project_data_frame(metaphors_url)
    date_range = pd.date_range(
        str(year) + '-9-1', str(year) + '-11-30', freq='D'
    )

    # Find the best-fit step-function model.
    # Load from disk if chkpt available.
    fits_path = 'fits{}.pickle'.format(year)
    if os.path.exists(fits_path):
        print('loading model fits for {} from disk'.format(year))
        with open(fits_path, 'br') as f:
            network_fits = pickle.load(f)
    else:
        print('fitting model for {} and saving to disk'.format(year))
        network_fits = fit_all_networks(viomet_df, date_range, iatv_corpus_name)
        with open(fits_path, 'wb') as f:
            pickle.dump(network_fits, f)

    # Partitions are of time into the ground and excited states.
    partition_infos = {
        network: network_fits[network][0]
        for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']
    }

    # Plot the three model fits (Figure 2).
    by_network_frequency_figure(
        viomet_df, date_range=date_range,
        iatv_corpus_name=iatv_corpus_name,
        partition_infos=partition_infos,
        save_path='ModelFits-{}.pdf'.format(year)
    )

    # Tabulate start/end excited state dates and frequencies
    # for each network (Table 1).
    pi_table = partition_info_table(viomet_df, date_range, partition_infos)
    print(pi_table)
    with open('Table1-{}.tex'.format(year), 'w') as f:
        pi_table.to_latex(f, escape=False,
                          formatters=FORMATTERS)

    # Tabulate frequencies for various word-network pairs (Table 2).
    net_word = by_network_word_table(viomet_df, date_range, partition_infos)
    print(net_word)
    with open('Table2-{}.tex'.format(year), 'w') as f:
        net_word.to_latex(f, formatters=FORMATTERS, escape=False)

    # Tabulate frequencies for various subject/object-network pairs (Table 3).
    if year == 2012:
        subjects = ['Barack Obama', 'Mitt Romney']
        objects = ['Barack Obama', 'Mitt Romney']
    elif year == 2016:
        subjects = ['Hillary Clinton', 'Donald Trump']
        objects = ['Hillary Clinton', 'Donald Trump']

    net_subobj = by_network_subj_obj_table(
        viomet_df, date_range, partition_infos,
        subjects=subjects, objects=objects
    )
    print(net_subobj)
    with open('Table3-{}.tex'.format(year), 'w') as f:
        net_subobj.to_latex(f, formatters=FORMATTERS, escape=False)

    network_fits_tables = model_fits_table(
        viomet_df, date_range, network_fits, top_n=20)
    networks = ['MSNBCW', 'CNNW', 'FOXNEWSW']

    for network in networks:
        fits_table = network_fits_tables[network]
        fname = 'SupplementTables/Table1-{}-{}.tex'.format(year, network)
        with open(fname, 'w') as f:
            fits_table.to_latex(f, index=False, formatters=FORMATTERS, escape=False)
