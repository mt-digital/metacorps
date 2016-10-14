#: extract datetime from filename; returns datetime.datetime
import re
import numpy as np

from datetime import datetime

re_dt = re.compile(r'^.*(201210\d{2}_\d{6}).*$')
re_name = re.compile('^.*201210\d{2}_\d{6}_(.*).cc5.srt$')


@np.vectorize
def extract_datetime(fname):

    m = re.match(re_dt, fname)

    return datetime.strptime(m.groups()[0], '%Y%m%d_%H%M%S')


@np.vectorize
def extract_program_name(fname):

    m = re.match(re_name, fname)

    return ' '.join(m.groups()[0].split('_'))
