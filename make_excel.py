'''
P&T and I discussed some words that are indicative of violent figurative
speech. We need to review the usage in the corpus in order to say whether
or not violent verbs and violent imagery was used literally or figuratively.
To do this, I'm going to make an Excel file with a few sheets, each of which
will be to review one of the following words:

    * hit
    * attack
    * knockout
    * punch
    * knock
    * (take a swing), swung
    * strick (struck)
    * bloody
    * combat
    * slug
    * smack

As a first pass, I'll just try to get hit and attack. As in building the PDF,
I'm going to focus on the debate month.
'''

import progressbar
import re

from collections import OrderedDict
from glob import glob
from pandas import DataFrame, ExcelWriter

from iatv.iatv import _make_ts_from_clips

g = glob('data/iatv-2012-debate-cycle/*201210*')

words = [
    w.upper() for w in
    [' hit ', 'attack', ' knockout ', ' punch', ' knock', 'blood',
     'struck', 'strike', ]
]

words_match_dict = {
    w: OrderedDict({
        'context': [],
        'code': [],
        'conceptual metaphor': [],
        'source domain': [],
        'target domain': [],
        'speaker': [],
        'reviewer': [],
        'description': [],
        'filename': [],
    })
    for w in words
}

# set up to ignore re-runs
re_id_tup = re.compile(
    r'^data/iatv-2012-debate-cycle/(.*)_(\d{8})_\d{6}_(.*).cc[1235].srt$'
)

# add processed ids to list and check if id is already in list
processed_id_tuples = []
no_match_filenames = []

empty_cols = [
    'code', 'conceptual metaphor', 'source domain', 'target domain',
    'reviewer', 'description', 'speaker'
]

bar = progressbar.ProgressBar()
for f in bar(g):

    m = re.match(re_id_tup, f)
    if m is not None:
        current_id_tuple = m.groups()
    else:
        no_match_filenames.append(f)

    if current_id_tuple not in processed_id_tuples and m is not None:

        processed_id_tuples.append(current_id_tuple)

        ts = _make_ts_from_clips(open(f).read())

        for l in ts:
            for w in words:
                if w in l:
                    if l not in words_match_dict[w]['context']:

                        words_match_dict[w]['filename'].append(f)

                        l = l.lower()
                        l = l.replace(w.lower(), w)
                        words_match_dict[w]['context'].append(l)

                        for col in empty_cols:
                            words_match_dict[w][col].append('')

writer = ExcelWriter('review.xlsx', engine='xlsxwriter')
workbook = writer.book

# formatters
context_fmt = workbook.add_format(
    {
        'text_wrap': True,
        'font_size': 14,
        'font_name': 'Cambria'
    }
)

annotations_fmt = workbook.add_format(
    {
        'text_wrap': True,
        'font_size': 12
    }
)


for w in words:
    DataFrame(words_match_dict[w]).to_excel(
        writer, index=False, sheet_name=w, columns=[
            'context', 'code', 'conceptual metaphor', 'source domain',
            'target domain', 'description', 'speaker', 'reviewer', 'filename'
        ]
    )
    worksheet = writer.sheets[w]
    worksheet.set_column('A:A', 120, context_fmt)
    worksheet.set_column('C:H', 90, annotations_fmt)

writer.save()

print(
    'Processing complete. List of filenames not matching regex:\n' +
    '\n'.join(no_match_filenames)
)
