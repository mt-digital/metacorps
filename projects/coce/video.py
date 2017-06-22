import os
import shutil

from iatv.iatv import Show

from collections import namedtuple


VideoInfo = namedtuple('VideoInfo', ['iatv_id', 'start_time', 'stop_time'])


VIDEO_INFO_LISTS = {
    'Ted Cruz': [
        VideoInfo(
            'CSPAN_20160316_002800_March_15_Primaries_Results_and_Speeches',
            8580,
            8640
        ),
        VideoInfo(
            'FOXNEWSW_20160423_160000_Americas_Election_HQ',
            960,
            1020
        ),
        VideoInfo(
            'CSPAN_20151220_200800_Washington_This_Week',
            1120,
            1220
        ),
        VideoInfo(
            'FOXNEWSW_20160328_040000_On_the_Record_With_Greta_Van_Susteren',
            2100,
            2160
        ),
        VideoInfo(
            'KTVN_20160224_023000_Channel_2_News_630PM',
            330,
            450
        ),
        VideoInfo(
            'CSPAN_20160201_150000_Key_Capitol_Hill_Hearings',
            1050,
            1160
        )
    ],

    'Donald Trump': [
        VideoInfo(
            'CSPAN2_20161011_022500_Donald_Trump_Campaigns_in_Ambridge_Pennsylvania',
            240,
            320
        ),
        VideoInfo(
            'CSPAN_20161107_060800_Donald_Trump_Holds_Rally_in_Sioux_City_Iowa',
            1260,
            1380
        ),
        VideoInfo(
            'KGAN_20160918_153000_Iowa_In_Focus',
            50,
            120
        ),
        VideoInfo(
            'KQED_20161010_010000_PBS_NewsHour_Debates_2016_A_Special_Report',
            5340,
            5420
        ),
        VideoInfo(
            'CSPAN3_20160915_150000_Politics_and_Public_Policy_Today',
            4200,
            4360
        ),
        VideoInfo(
            'CNBC_20170328_190000_Closing_Bell',
            30,
            120
        )
    ],

    'Other': [
        VideoInfo(
            'COM_20170420_084000_The_Daily_Show',
            1600,
            1680
        ),
        VideoInfo(
            'FBC_20161029_070000_Lou_Dobbs_Tonight',
            340,
            460
        ),
        VideoInfo(
            'MSNBCW_20161223_080000_All_In_With_Chris_Hayes',
            640,
            750
        ),
        VideoInfo(
            'CSPAN2_20170119_233600_Energy_Secretary_Nominee_Rick_Perry_Testifies_at_Confirmation_Hearing',
            2940,
            3060
        ),
        VideoInfo(
            'MSNBCW_20160316_030000_The_Place_for_Politics_2016',
            2920,
            3040
        ),
        VideoInfo(
            'CSPAN_20170326_233000_Vice_President_Pence_on_Supreme_Court_Nominee_Neil_Gorsuch',
            1020,
            1100
        )

    ]
}


def download_all():

    for speaker in ['Ted Cruz', 'Donald Trump', 'Other']:
        print('Downloading ' + speaker)
        download_videos(speaker)


def download_videos(spoken_by,
                    download_dir=None):
    '''
    Overwrites existing download_dir if it exists
    '''

    # set default download_dir if not provided
    if download_dir is None:
        download_dir = os.path.expanduser(
            os.path.join('~', 'Desktop', spoken_by.replace(' ', ''))
        )

    # overwrite if it exists
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)

    os.mkdir(download_dir)

    _download_list(VIDEO_INFO_LISTS[spoken_by], download_dir)


def _download_list(video_info_list, download_dir):

    for video_info in video_info_list:

        download_path = os.path.join(download_dir, video_info.iatv_id + '.mp4')

        Show(
            video_info.iatv_id
        ).download_video(
            video_info.start_time, video_info.stop_time,
            download_path=download_path
        )
