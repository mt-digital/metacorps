import numpy as np
import pandas as pd

from app.models import Project


def speaker_counts(analyzer_df,
                   speakers_of_interest=['Ted Cruz', 'Donald Trump'],
                   resample_period='1M'):
    '''
    analyzer_df comes from get_analyzer
    '''
    # fill in details for repeat quotes
    analyzer_df = _fill_repeat(analyzer_df)

    import ipdb
    ipdb.set_trace()

    sb = analyzer_df[['start_localtime', 'spoken_by']]

    # only if the speaker is not any of the speakers_of_interest do we mark
    # it as 'Other'
    others_index = np.sum(
        [sb.spoken_by != speaker for speaker in speakers_of_interest],
        axis=0
    )
    sb.loc[others_index == len(speakers_of_interest), 'spoken_by'] = 'Other'

    sb_piv = sb.groupby(
            ['start_localtime', 'spoken_by']
        ).size().to_frame('count').reset_index().pivot(
            index='start_localtime', columns='spoken_by', values='count'
        )

    sb_piv.fillna(0.0, inplace=True)
    return sb_piv.resample(resample_period).sum()


def _fill_repeat(analyzer_df,
                 project_name='test epa proj',
                 facet_word='epa-kill'):
    '''
    Look up referenced instance for each repeated quote and fill in information
    for each repeated quote.
    '''
    adf = analyzer_df
    repeat_quote_rows = adf[adf.repeat]

    repeat_of = repeat_quote_rows.repeat_index
    repeat_of.dropna(inplace=True)

    # XXX need to subtract one because I foolishly am adding 1 on the metacorps
    # frontend XXX
    repeat_of = repeat_of.apply(int) - 1

    # need to read info from database since adf doesn't have proper indices
    project = next(p for p in Project.objects if p.name == 'test epa proj')
    facet = next(f for f in project.facets if f.word == facet_word)
    instances = facet.instances

    replacements = pd.DataFrame(
        data=[inst.to_mongo() for inst in instances]
    ).ix[repeat_of]

    # replacements = instances[repeat_of]

    replacements.index = repeat_of.index

    repl_cols = ['conceptual_metaphor', 'spoken_by', 'subjects', 'objects',
                 'active_passive', 'tense']

    adf.loc[adf.repeat, repl_cols] = replacements[repl_cols]

    import ipdb
    ipdb.set_trace()

    return adf
