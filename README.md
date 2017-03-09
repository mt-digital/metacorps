# _metacorps_

Metacorps is a web application and data processing pipeline for coding and
analyzing metaphor use in the wild. Currently metacorps is specialized in 
subtle ways to be used with internet archive data. In the long term, metacorps
will be made more general so diverse sources can be used. If you would like
to analyze [Internet Archive Cable News](http://archive.org/tv/details) data,
you can use my [iatv](http://github.com/mtpain/iatv) python package.

## Loading IATV data into metacorps

The follwing instructions assume you have downloaded transcripts 
from the TV News Archive using `iatv`, which looks something like this,

```python
from iatv import search_items, download_all_transcripts

# search for everything on Fox News in August, 2016
items = search_items('I', channel='FOXNEWSW', time='201608', rows=1000)
# remove commercials
shows = [item for items if 'commercial' not in item]
# download all shows to either existing or new directory
download_all_transcripts(shows, base_directory='FOXNEWSW-201608')
```

Also, you must tell Flask where to find your configuration file. You'll be using
models from the metacorps flask application.

```
export CONFIG_FILE='conf/default.cfg'
```

Then to insert these into your *metacorps* database, 

```python
from insert_iatv_docs import (
    build_iatv_corpus, make_project, DEFAULT_VIOLENCE_LIST
)

# excluding kwarg program_names, which would restrict which shows are inserted
august_corpus = build_iatv_corpus(
    datetime(2016, 8, 1), datetime(2016, 8, 31, 11, 59), 'August 2016'
)

# save if you want to persist this IatvDocument collection; not necessary
august_corpus.save()

august_docs = august_corpus.documents

# metacorps looks for pairs of words and word stems, which could be metaphor
p = make_project(
    'My project - August 2016', august_docs, DEFAULT_VIOLENCE_LIST
)
# save then check your running metacorps instance for an updated list
p.save()
```
