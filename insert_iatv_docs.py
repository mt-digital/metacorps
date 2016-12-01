'''
Insert documents from folder into the iatv_documents
collection in the metacorps database. That database is set by Flask
and flask-mongoengine in the
Flask config given in app.py for development purposes at this time.

After the documents are inserted then various corpora can be made from
those documents either interactively or with another script/function
'''
import json
import re

from datetime import datetime
from glob import glob
from os.path import join as opjoin

from app.models import IatvDocument, IatvCorpus, Instance, Facet, Project


DEFAULT_DEBATE_PROGRAMS = [
    'Piers Morgan Tonight', 'Anderson Cooper 360', 'The O\'Reilly Factor',
    'Hannity', 'Hardball With Chris Matthews', 'The Rachel Maddow Show'
]


def build_iatv_corpus(start_datetime, stop_datetime,
                      corpus_name, program_names=DEFAULT_DEBATE_PROGRAMS):
    '''
    Build corpus for a given year and a set of networks.

    Arguments:
        start_datetime (datetime.datetime): datetime equal/after which shows
            should be taken
        stop_datetime (datetime.datetime): datetime equal/before which shows
            should be taken
        corpus_name (str): descriptive name for the corpus for future discovery
        programs (dict): Dictionary of {station: [programs]}

    Returns:
        (IatvCorpus): Newly created corpus
    '''
    corpus_docs = IatvDocument.objects(
        program_name__in=program_names, start_localtime__gte=start_datetime,
        start_localtime__lte=stop_datetime
    )

    corpus = IatvCorpus(name=corpus_name, documents=corpus_docs)

    return corpus


# ¿ Should only a single corpus be used ? If you want to add support for
# another, only need to build documents ahead of time, then do
# for doc in documents instead of pulling directly form corpus. Then instead
# of a corpus name pass the corpora of interest, then pull out documents.
# or just pull out relevant documents from a corpus ahead of time
def make_project(project_name, documents, word_regex_pairs):
    '''

    Arguments:
        project_name (str)
        corpus_name (str)
        word_regex_pair list((str, str)): list ofpair of word
            and regex representation to
            use in searching for instances, used mostly for irregular verbs,
            such as ('strike', r'str(uck|ike)')
    Returns:
        (Project): A newly instantiated project with facets and instances for
            all
    '''
    # raises error if it does not exist, as we'd like

    # documents = IatvCorpus.objects.get(name=corpus_name).documents

    project = Project(name=project_name)

    for wr_pair in word_regex_pairs:

        facet = Facet(word=wr_pair[0])
        # regex = re.compile(wr_pair[1])

        processed_prog_dates = []

        for doc in documents:

            prog_date = (doc.program_name, doc.start_localtime.date())

            if prog_date not in processed_prog_dates:

                processed_prog_dates.append(prog_date)
                for line in doc.document_data.split('\n'):

                    if wr_pair[1] in line:
                        facet.instances.append(
                            Instance(text=line, source_id=doc.id,
                                     reference_url=doc.iatv_url)
                        )

        facet.total_count = len(facet.instances)

        project.facets.append(facet)

    return project


def insert_iatv_docs(folder):

    g = glob(folder + '/*')

    for _dir in g:

        try:
            _import_iatv_blob(_dir)

        except Exception as e:
            print('Error importing from directory(?) ' + _dir)
            try:
                print('Exception:\n' + e.message)
            except:
                pass


def _import_iatv_blob(_dir):

    # read as much information as possible from metadata
    md_str = open(opjoin(_dir, 'metadata.json')).read()
    metadata = json.loads(md_str)

    iatv_id = metadata['identifier']

    if len(IatvDocument.objects(iatv_id=iatv_id)) == 0:
        iatv_url = metadata['identifier-access'][0]

        try:
            start_localtime = _mdtime_to_datetime(metadata['start_localtime'][0])
            start_time = _mdtime_to_datetime(metadata['start_time'][0])
            stop_time = _mdtime_to_datetime(metadata['stop_time'][0])

            runtime_seconds = (stop_time - start_time).seconds
            utc_offset = metadata['utc_offset'][0]

        except Exception as e:
            print('Error accessing dates for directory ' + _dir)
            print('Exception:\n' + e.message)

        title = metadata['title']
        tspl = title.split(':')

        program_name = tspl[0].strip()
        network = tspl[1].strip()

        # now read text and SRT files
        text = open(opjoin(_dir, 'transcript.txt')).read()

        srt_path = opjoin(_dir, iatv_id + '.cc5.srt')
        raw_srt = open(srt_path, 'r').read()
        doc = IatvDocument(document_data=text, raw_srt=raw_srt,
                           iatv_id=iatv_id, iatv_url=iatv_url,
                           start_localtime=start_localtime, start_time=start_time,
                           stop_time=stop_time, runtime_seconds=runtime_seconds,
                           utc_offset=utc_offset, program_name=program_name,
                           network=network)

        doc.save()


def _mdtime_to_datetime(mdtime):
    fmt_str = '%Y-%m-%d %H:%M:%S'
    return datetime.strptime(mdtime, fmt_str)
