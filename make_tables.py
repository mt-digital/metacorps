import pickle
import os

import pandas as pd

from projects.viomet.analysis import (
    by_network_subj_obj_table, by_network_word_table,
    fit_all_networks, partition_info_table
)
from projects.common import get_project_data_frame

METAPHORS_URL = \
    "http://metacorps.io/static/data/viomet-2012-snapshot-project-df.csv"

# TODO iterate over [2012, 2016]; requires a 2016 project snapshot.
YEAR = 2012
SYEAR = str(YEAR)
IATV_CORPUS_NAME = 'Viomet Sep-Nov ' + SYEAR

FORMATTERS = {
    '$f^g$': '{:,.2f}'.format,
    '$f^e$': '{:,.2f}'.format,
    'totals': lambda n: '{:, d}'.format(int(n)),
    '\% change': '{:,.1f}'.format
}

viomet_df = get_project_data_frame(METAPHORS_URL)
date_range = pd.date_range(str(YEAR) + '-9-1', str(YEAR) + '-11-30', freq='D')

# Get model fits for all possible temporal partitions. Load from disk if avail.
fits_path = 'fits{}.pickle'.format(YEAR)
if os.path.exists(fits_path):
    with open(fits_path, 'br') as f:
        fits = pickle.load(f)
else:
    # This is the *only* (double checked) part that uses the IATV_CORPUS_NAME.
    fits = fit_all_networks(viomet_df, date_range, IATV_CORPUS_NAME)
    with open(fits_path, 'wb') as f:
        pickle.dump(fits, f)

partition_infos = {
    network: fits[network][0]
    for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']
}

pi_table = partition_info_table(viomet_df, date_range, partition_infos)
print(pi_table)
with open("Table1.tex", 'w') as f:
    pi_table.to_latex(f, escape=False,
                      formatters=FORMATTERS)

net_word = by_network_word_table(viomet_df, date_range, partition_infos)
print(net_word)
with open("Table2.tex", 'w') as f:
    net_word.to_latex(f, formatters=FORMATTERS, escape=False)

net_subobj = by_network_subj_obj_table(viomet_df, date_range, partition_infos)
print(net_subobj)
with open('Table3.tex', 'w') as f:
    net_subobj.to_latex(f, formatters=FORMATTERS, escape=False)
