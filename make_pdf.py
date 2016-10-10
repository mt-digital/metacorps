'''
For now this will just make a PDF of the 2012 debates and the associated
news coverage of them. Later it could turn into a tool of its own or not,
we'll see.

Outline:
    1. amass and process all closed captions from IATV share; put into
        dict indexed by date and show name
    2.
'''

import os
import re

from glob import glob
from datetime import datetime

from iatv.iatv import _make_ts_from_clips


# initialize markdown file
write_f = open('2012-debate-cycle.md', 'w')

# make document title
write_f.write('% 2012 Debate Cycle Coverage\n')
write_f.write('% Compiled by Matthew Turner\n')
write_f.write('% ' + datetime.now().strftime('%D') + '\n')

# add debates
write_f.write('# The Debates\n\n')

debate_files = [
    os.path.join('data', 'debates', '2012', 'october{}.md'.format(d))
    for d in ['3', '11-vp', '16', '22']
]

for d in debate_files:
    write_f.write(
        open(d).read() + '\n\n'
    )


def opj_datadir(glob_patt):

    return os.path.join(
        'data', 'iatv-2012-debate-cycle', glob_patt
    )


solr_dates = [
    '201210' + str(day) if day > 9 else '2012100' + str(day)
    for day in range(1, 32)
]

#: extract datetime from filename; returns datetime.datetime
re_dt = re.compile(r'^.*(201210\d{2}_\d{6}).*$')


def extract_datetime(fname):

    m = re.match(re_dt, fname)

    return datetime.strptime(m.groups()[0], '%Y%m%d_%H%M%S')

#: regex for extracting show name
re_name = re.compile('^.*201210\d{2}_\d{6}_(.*).cc5.srt$')


def extract_program_name(fname):

    m = re.match(re_name, fname)

    return ' '.join(m.groups()[0].split('_'))

# now write the transcripts for cable news coverage
write_f.write('# Cable News Coverage\n\n')

for d in solr_dates:

    shows_date = datetime.strptime(d, '%Y%m%d')

    write_f.write(
        shows_date.strftime('## %A, %B %d, %Y \n\n').replace(' 0', ' ')
    )

    for f in glob(opj_datadir('*' + d + '*.cc5.srt')):

        # extract datetime for show
        dte = extract_datetime(f)

        # extract show name
        program_name = extract_program_name(f)

        write_f.write(
            '### ' + program_name + ' ' + dte.strftime('%I:%M %p') + '\n\n'
        )

        srt = open(f, 'r', encoding='utf8', errors='ignore').read()
        ts_list = _make_ts_from_clips(srt.replace(u'\ufeff', ''))

        ts = '\n\n'.join(ts_list)

        write_f.write(ts + '\n\n')

write_f.close()
