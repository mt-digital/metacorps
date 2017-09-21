import pandas as pd
import numpy as np

from datetime import datetime, date
from nose.tools import ok_

from app.models import IatvCorpus, IatvDocument
from projects.common.analysis import (
    _count_by_start_localtime, daily_metaphor_counts, shows_per_date,
    daily_frequency
)
from projects.viomet.analysis import PartitionInfo, partition_sums


def _gen_test_input(pn, n, fw, so):

    rows = [
        # Tracy Morgan on CNN says "kill" and "punch"
        # aired 9/1/16 at 21:00/9pm
        (datetime(2016, 9, 1, 21), pn[0], n[1], fw[0], so[0]),
        (datetime(2016, 9, 1, 21), pn[0], n[1], fw[2], so[0]),

        # Dingbat Alley on MSNBC says "kill", "punch", and "attack"
        # aired 9/2/16 at 20:00/8pm
        (datetime(2016, 9, 2, 20), pn[1], n[0], fw[0], so[1]),
        (datetime(2016, 9, 2, 20), pn[1], n[0], fw[2], so[2]),
        (datetime(2016, 9, 2, 20), pn[1], n[0], fw[3], so[1]),

        # iCry Sad News on MSNBC says "kill" and "murder"
        # aired 9/2/16 at 18:00/6pm
        (datetime(2016, 9, 2, 18), pn[2], n[0], fw[0], so[1]),
        (datetime(2016, 9, 2, 18), pn[2], n[0], fw[1], so[3]),

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

    return input_df


def test_count_for_each_local_time():
    '''
    testing initial groupby in _count_by_start_localtime
    '''
    pn = [
        'Tracy Morgans news hour', 'Dingbat Alley', 'iCry Sad News Time',
        'Digging Turnips with Ethan Land', 'Good morning, middle america!'
    ]
    n = ['CNNW', 'MSNBCW', 'FOXNEWSW']
    fw = ['kill', 'murder', 'punch', 'attack']
    so = ['trump', 'clinton', 'obama', 'media']

    input_df = _gen_test_input(pn, n, fw, so)

    # TEST PROGRAM NAME-NETWORK GROUPINGS

    # test how it works on subjects and networks groupby and count
    prog_network_output_columns = [
        'start_localtime', 'program_name', 'network', 'counts'
    ]
    expected_prog_network_output = pd.DataFrame(
        data=[
            (datetime(2016, 9, 1, 6),  pn[4], n[2], 1),
            (datetime(2016, 9, 1, 21), pn[0], n[1], 2),
            (datetime(2016, 9, 2, 6),  pn[4], n[2], 1),
            (datetime(2016, 9, 2, 18), pn[2], n[0], 2),
            (datetime(2016, 9, 2, 20), pn[1], n[0], 3),
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
            (datetime(2016, 9, 1, 21), n[1], 2),
            (datetime(2016, 9, 2, 6),  n[2], 1),
            (datetime(2016, 9, 2, 18), n[0], 2),
            (datetime(2016, 9, 2, 20), n[0], 3),
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


def test_daily_metaphor_counts():
    '''
    Convert an Analysis.df to be daily timeseries of network usage
    '''
    pn = [
        'Tracy Morgans news hour', 'Dingbat Alley', 'iCry Sad News Time',
        'Digging Turnips with Ethan Land', 'Good morning, middle america!'
    ]
    n = ['MSNBCW', 'CNNW', 'FOXNEWSW']
    fw = ['kill', 'murder', 'punch', 'attack']
    so = ['trump', 'clinton', 'obama', 'media']

    input_df = _gen_test_input(pn, n, fw, so)

    date_index = pd.date_range('2016-9-1', '2016-9-4', freq='D')
    expected_network_output = pd.DataFrame(
        index=date_index,
        data=[
            (0, 2, 1),
            (5, 0, 1),
            (0, 0, 2),
            (0, 0, 2),
        ],
        columns=pd.Index(n, name='network'),
        dtype=np.float64  # necessary to explicitly match data types
                          # can't seem to change dtypes in pivot table
    )

    date_index = pd.date_range('2016-9-1', '2016-9-4', freq='D')

    # put columns in the same order for comparison
    network_output = daily_metaphor_counts(input_df, date_index, by=['network'])[n]

    pd.testing.assert_frame_equal(expected_network_output, network_output)


def _setup_iatv_corpus(iatv_corpus_name):

    # programs = {
    #     'MSNBCW': ['Dingbat Alley', 'iCry Sad News Time'],
    #     'CNNW': ['Tracy Morgans news hour'],
    #     'FOXNEWSW': ['Digging Turnips', 'Good morning, middle america!']
    # }

    # build IatvDocument instances to be part of the IatvCorpus
    # one or two for each day for each network
    fake_id = 'XXX123'
    fake_data = 'this is a show'
    fake_url = 'http://www.iatv.yo/XXX123'

    docs = [
        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='MSNBCW',
            program_name='Dingbat Alley',
            start_localtime=datetime(2016, 9, 1, 20)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='MSNBCW',
            program_name='Dingbat Alley',
            start_localtime=datetime(2016, 9, 2, 20)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='MSNBCW',
            program_name='Dingbat Alley',
            start_localtime=datetime(2016, 9, 3, 20)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='MSNBCW',
            program_name='iCry Sad News Time',
            start_localtime=datetime(2016, 9, 1, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='MSNBCW',
            program_name='iCry Sad News Time',
            start_localtime=datetime(2016, 9, 2, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='CNNW',
            program_name='Tracy Morgan news hour',
            start_localtime=datetime(2016, 9, 1, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='CNNW',
            program_name='Tracy Morgan news hour',
            start_localtime=datetime(2016, 9, 4, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Digging Turnips',
            start_localtime=datetime(2016, 9, 2, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Digging Turnips',
            start_localtime=datetime(2016, 9, 3, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Digging Turnips',
            start_localtime=datetime(2016, 9, 4, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Good morning, middle america!',
            start_localtime=datetime(2016, 9, 1, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Good morning, middle america!',
            start_localtime=datetime(2016, 9, 2, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Good morning, middle america!',
            start_localtime=datetime(2016, 9, 3, 18)
        ),

        IatvDocument(
            document_data=fake_data,
            iatv_id=fake_id,
            iatv_url=fake_url,
            network='FOXNEWSW',
            program_name='Good morning, middle america!',
            start_localtime=datetime(2016, 9, 4, 18)
        )
    ]

    for doc in docs:
        doc.save()

    return docs


def _setup_mongo():

    test_corpus_name = 'Test ' + datetime.now().isoformat()[:-7]

    docs = _setup_iatv_corpus(test_corpus_name)

    ic = IatvCorpus(name=test_corpus_name, documents=docs)

    ic.save()

    return test_corpus_name


def _teardown_mongo(test_corpus_name):

    ic = IatvCorpus.objects(name=test_corpus_name)[0]
    # iterate over all documents and remove
    for doc in ic.documents:
        IatvDocument.objects(pk=doc.pk)[0].delete()

    ic.delete()


def test_shows_per_day():
    '''
    Insert some shows into the database using the program names (pn) and
    networks (n) from other parts of the tests.

    XXX these program names associated with a network should be in
    a dictionary to avoid straining my brain remembering which network went
    with which program name XXX
    '''
    test_corpus_name = _setup_mongo()

    ic = IatvCorpus.objects(name=test_corpus_name)[0]

    date_index = pd.date_range('2016-9-1', '2016-9-4', freq='D')

    expected_spd = pd.Series(
        index=date_index,
        data=[4, 4, 3, 3],
        dtype=np.float64
    )
    spd = shows_per_date(date_index, ic)

    pd.testing.assert_series_equal(expected_spd, spd)

    expected_spd_by_network = pd.DataFrame(
        index=date_index,
        data={
            'MSNBCW':   [2, 2, 1, 0],
            'CNNW':     [1, 0, 0, 1],
            'FOXNEWSW': [1, 2, 2, 2]
        },
        dtype=np.float64
    )
    spd_by_network = shows_per_date(date_index, ic, by_network=True)

    pd.testing.assert_frame_equal(expected_spd_by_network, spd_by_network)

    _teardown_mongo(test_corpus_name)


def test_daily_frequency():

    test_corpus_name = _setup_mongo()
    date_index = pd.date_range('2016-9-1', '2016-9-4', freq='D')
    ic = IatvCorpus.objects(name=test_corpus_name)[0]

    # obtained by dividing total metaphor counts by total shows per day
    expected_metaphor_freq_all = pd.DataFrame(
        index=date_index, data={'freq': [.75, 1.5, 2.0/3.0, 2.0/3.0]}
    )

    pn = [
        'Tracy Morgans news hour', 'Dingbat Alley', 'iCry Sad News Time',
        'Digging Turnips with Ethan Land', 'Good morning, middle america!'
    ]
    n = ['MSNBCW', 'CNNW', 'FOXNEWSW']
    fw = ['kill', 'murder', 'punch', 'attack']
    so = ['trump', 'clinton', 'obama', 'media']

    input_df = _gen_test_input(pn, n, fw, so)
    daily_freq = daily_frequency(input_df, date_index, ic)

    pd.testing.assert_frame_equal(daily_freq, expected_metaphor_freq_all)

    daily_freq_by_network = daily_frequency(
        input_df, date_index, ic, by=['network']
    )[['MSNBCW', 'CNNW', 'FOXNEWSW']]

    expected_metaphor_freq_by_network = pd.DataFrame(
        index=date_index,
        data=[
            (0, 2, 1),
            (2.5, np.nan, .5),
            (0, np.nan, 1),
            (np.nan, 0, 1)
        ],
        dtype=np.float64,
        columns=pd.Index(['MSNBCW', 'CNNW', 'FOXNEWSW'], name='network')
    )

    pd.testing.assert_frame_equal(
        daily_freq_by_network, expected_metaphor_freq_by_network
    )


def test_partition_sum():
    '''
    Given a dataframe with counts for 'All' or network columns, calculate sum of each partition for each column
    '''
    partition_infos = {
        'MSNBCW': PartitionInfo(datetime(2016, 9, 1), datetime(2016, 9, 2), 1, 2.4),
        'CNNW': PartitionInfo(datetime(2016, 9, 2), datetime(2016, 9, 4), 2, 2.4),
        'FOXNEWSW': PartitionInfo(datetime(2016, 9, 2), datetime(2016, 9, 4), 1.5, 2),
        'All':    PartitionInfo(datetime(2016, 9, 1), datetime(2016, 9, 3), 1, 3.0)
    }

    date_index = pd.date_range('2016-9-1', '2016-9-5', freq='D')

    # generate input_df
    pn = [
        'Tracy Morgans news hour', 'Dingbat Alley', 'iCry Sad News Time',
        'Digging Turnips with Ethan Land', 'Good morning, middle america!'
    ]
    n = ['MSNBCW', 'CNNW', 'FOXNEWSW']
    fw = ['kill', 'murder', 'punch', 'attack']
    so = ['trump', 'clinton', 'obama', 'media']

    input_df = _gen_test_input(pn, n, fw, so)

    counts_df = daily_metaphor_counts(input_df, date_index, by=['network'])[n]

    expected_df = pd.DataFrame(
        index=['MSNBCW', 'CNNW', 'FOXNEWSW', 'All'],
        data={'ground': [0, 2, 1, 2], 'excited': [5, 0, 5, 11]},
        dtype=np.float64
    )
    expected_df = expected_df[['ground', 'excited']]

    psums = partition_sums(counts_df, partition_infos)

    pd.testing.assert_frame_equal(psums, expected_df)


def test_byweekday_frequency():
    '''
    Give the frequency per weekday for each network and all networks total
    '''
    # make index days of the week in order starting Sunday

    # groupby days of the week? maybe need a column with days of week, then gb

    assert False


def test_subject_object_counts_per_partition():
    '''
    Given partition dates and analyzer, count subject and object
    '''
    assert False
