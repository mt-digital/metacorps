import pandas as pd
import numpy as np

from datetime import datetime
from nose.tools import ok_, eq_

from projects.viomet.analysis import _count_by_start_localtime


def test_count_for_each_local_time():
    '''
    testing initial groupby in _count_by_start_localtime
    '''
    pn = [
        'Tracy Morgans news hour', 'Dingbat Alley', 'iCry Sad News Time',
        'Digging Turnips with Ethan Land', 'Good morning, middle america!'
    ]
    n = ['CNN', 'MSNBC', 'Fox News']
    fw = ['kill', 'murder', 'punch', 'attack']
    so = ['trump', 'clinton', 'obama', 'media']

    rows = [
        # Tracy Morgan on CNN says "kill" and "punch"
        # aired 9/1/16 at 21:00/9pm
        (datetime(2016, 9, 1, 21), pn[0], n[0], fw[0], so[0]),
        (datetime(2016, 9, 1, 21), pn[0], n[0], fw[2], so[0]),

        # Dingbat Alley on MSNBC says "kill", "punch", and "attack"
        # aired 9/2/16 at 20:00/8pm
        (datetime(2016, 9, 2, 20), pn[1], n[1], fw[0], so[1]),
        (datetime(2016, 9, 2, 20), pn[1], n[1], fw[2], so[2]),
        (datetime(2016, 9, 2, 20), pn[1], n[1], fw[3], so[1]),

        # iCry Sad News on MSNBC says "kill" and "murder"
        # aired 9/2/16 at 18:00/6pm
        (datetime(2016, 9, 2, 18), pn[2], n[1], fw[0], so[1]),
        (datetime(2016, 9, 2, 18), pn[2], n[1], fw[1], so[3]),

        # Digging Turnips on Fox News says "kill", "murder", and "attack"
        # aired 9/3 and 9/4 at 20:00/8pm
        (datetime(2016, 9, 3, 20), pn[3], n[2], fw[3], so[3]),
        (datetime(2016, 9, 3, 20), pn[3], n[2], fw[0], so[0]),

        (datetime(2016, 9, 4, 20), pn[3], n[2], fw[1], so[3]),

        # Good morning, middle america! on Fox News says "kill" and "punch"
        # aired 9/1, 9/2, and 9/4 at 6:00
        (datetime(2016, 9, 1, 6), pn[4], n[2], fw[2], so[1]),

        (datetime(2016, 9, 2, 6), pn[4], n[2], fw[2], so[1]),

        (datetime(2016, 9, 4, 6), pn[4], n[2], fw[0], so[0]),
    ]

    input_columns = ['start_localtime',
                     'program_name',
                     'network',
                     'facet_word',
                     'subjects']

    input_df = pd.DataFrame(rows, columns=input_columns)

    # TEST PROGRAM NAME-NETWORK GROUPINGS

    # test how it works on subjects and networks groupby and count
    prog_network_output_columns = [
        'start_localtime', 'program_name', 'network', 'counts'
    ]
    expected_prog_network_output = pd.DataFrame(
        data=[
            (datetime(2016, 9, 1, 6),  pn[4], n[2], 1),
            (datetime(2016, 9, 1, 21), pn[0], n[0], 2),
            (datetime(2016, 9, 2, 6),  pn[4], n[2], 1),
            (datetime(2016, 9, 2, 18), pn[2], n[1], 2),
            (datetime(2016, 9, 2, 20), pn[1], n[1], 3),
            (datetime(2016, 9, 3, 20), pn[3], n[2], 2),
            (datetime(2016, 9, 4, 6),  pn[4], n[2], 1),
            (datetime(2016, 9, 4, 20), pn[3], n[2], 1),
        ],
        columns=prog_network_output_columns
    )

    prog_network_output = _count_by_start_localtime(
        input_df, prog_network_output_columns[1:-1]
    )

    ok_(expected_prog_network_output.equals(prog_network_output),
        '\n'.join([
                str(prog_network_output),
                str(prog_network_output == expected_prog_network_output)
                ]
            )
        )

    # TEST NETWORK GROUPINGS
    network_output_columns = [
        'start_localtime', 'network', 'counts'
    ]

    expected_network_output = pd.DataFrame(
        data=[
            (datetime(2016, 9, 1, 6),  n[2], 1),
            (datetime(2016, 9, 1, 21), n[0], 2),
            (datetime(2016, 9, 2, 6),  n[2], 1),
            (datetime(2016, 9, 2, 18), n[1], 2),
            (datetime(2016, 9, 2, 20), n[1], 3),
            (datetime(2016, 9, 3, 20), n[2], 2),
            (datetime(2016, 9, 4, 6),  n[2], 1),
            (datetime(2016, 9, 4, 20), n[2], 1),
        ],
        columns=network_output_columns
    )

    network_output = _count_by_start_localtime(
        input_df, ['network']
    )

    ok_(expected_network_output.equals(network_output),
        '\n'.join([
                str(network_output),
                str(network_output == expected_network_output)
                ]
            )
        )

    # TEST SUBJECT GROUPINGS
    subject_output_columns = [
        'start_localtime', 'subjects', 'counts'
    ]

    expected_subject_output = pd.DataFrame(
        data=[
            (datetime(2016, 9, 1, 6),  so[1], 1),
            (datetime(2016, 9, 1, 21), so[0], 2),
            (datetime(2016, 9, 2, 6),  so[1], 1),
            (datetime(2016, 9, 2, 18), so[1], 1),
            (datetime(2016, 9, 2, 18), so[3], 1),
            (datetime(2016, 9, 2, 20), so[1], 2),
            (datetime(2016, 9, 2, 20), so[2], 1),
            (datetime(2016, 9, 3, 20), so[3], 1),
            (datetime(2016, 9, 3, 20), so[0], 1),
            (datetime(2016, 9, 4, 6),  so[0], 1),
            (datetime(2016, 9, 4, 20), so[3], 1),
        ],
        columns=subject_output_columns
    )

    subject_output = _count_by_start_localtime(
        input_df, ['subjects']
    )

    ok_(expected_subject_output.equals(subject_output),
        '\n'.join([
                str(subject_output),
                str(subject_output == expected_subject_output)
                ]
            )
        )
