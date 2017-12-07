# _metacorps_

Metacorps is a web application and data processing pipeline for coding and
analyzing metaphor use in the wild. Currently metacorps is specialized in 
subtle ways to be used with internet archive data. In the long term, metacorps
will be made more general so diverse sources can be used. If you would like
to analyze [Internet Archive Cable News](http://archive.org/tv/details) data,
you can use my [iatv](http://github.com/mtpain/iatv) python package.

## Building figures for the metaphorical violence paper

The most immediate goal of Metacorps is to provide a functional prototype
that powers rapid interactive identification and annotation of metaphor. 
More specifically, we are identifying and annotating metaphorical violence on
the cable news stations CNN, MSNBC, and Fox News. Part of the value of Metacorps
is as a full-lifecycle data pipeline, including the processing phase. For this,
we have a projects directory containing `common` and `viomet` subdirectories.
Each of these subdirectories have files `analysis.py` and `vis.py`, which 
provide functionality matching their names. Below are some notes on how
to use these to produce the publication-ready plots. It needs cleanup.

```python
import pandas as pd

from projects.common import get_project_data_frame
from projects.viomet.analysis import by_network_table
from viomet_9_10_17 import fit_all_networks

metaphors_url = \
    'http://metacorps.io/static/data/viomet-2012-snapshot-project-df.csv'
viomet_df = get_project_data_frame(metaphors_url)
date_range = pd.date_range('2012-9-1', '2012-11-30', freq='D')

iatv_corpus_name = 'Viomet Sep-Nov 2012'
network_fits = fit_all_networks(
        viomet_df, date_range=date_range, iatv_corpus_name, verbose=False
    )
partition_infos = {
    network: fit_2012[network][0] 
    for network in ['MSNBCW', 'CNNW', 'FOXNEWSW']
}

fit_2012 = fit_all_networks(
        viomet_df, date_range, iatv_corpus_name, verbose=False
    )

# Generate Table 2.
bnw_tbl_df = by_network_word_table(viomet_df, date_range, partition_infos)
print(bnw_tbl_df)
# Out[42]:
#                          $f^g$     $f^e$  total
# Violent Word Network
# hit          MSNBC     0.483333  0.833333   54.0
#             CNN       0.289474  0.428571   28.0
#             Fox News  0.303030  0.416667   30.0
# beat         MSNBC     0.566667  0.266667   42.0
#             CNN       0.381579  0.142857   31.0
#             Fox News  0.378788  0.166667   29.0
# attack       MSNBC     0.300000  0.466667   32.0
#             CNN       0.500000  1.357143   57.0
#             Fox News  0.803030  0.375000   62.0
```

## Run the app!

[metacorps.io](http://metacorps.io) is hosted and available for all. For 
development purposes, you can run the server locally. To run the server locally,
you need MongoDB installed and have mongod running. Google how to do this
if you don't know. You can customize the default template
`app/conf/default.cfg.template` or just use it directly when running locally,
as shown below

```
export CONFIG_FILE="conf/default.cfg.template"
```

```
export FLASK_APP="app/app.py"
```

```
flask run --with-threads --reload
```

The first flag on the last command tell the application to accept multiple 
connections at once, which seems to result in a better developer experience.
The second flag tells the application to reload automatically whenever a
source file changes. After running this visit http://localhost:5000 to 
see the metacorps home page. If you have not initialized it with any 
Projects there won't be any, just the user log.

## tests

To run tests, first edit the configuration template 
`app/conf/default.cfg.template` by renaming it to `app/conf/test.cfg` and
changing the contents to match the contents below. Changing the database
will save your development database from becoming cluttered with test
collections.

```conf
MONGODB_SETTINGS={'db': 'test-metacorps'}
DEBUG = False
SECRET_KEY = 'Change me or do not -- important thing is the database'
```



## Loading IATV data into metacorps from IATV search results

The ``Project`` class in [app/models.py](tree/master/app/models.py) provides a 
class method to ingest IATV search results into a project. See the example
below.

```python
from iatv import search_items
from app.models import Project

# following archive.org query format (see https://blog.archive.org/developers/)
econ_query = 'strangle+economy'
regulation_query = 'strangle+regulation'
time = '20151101-20170603'

# 2000 rows just to hopefully get all results; len(items) should be inspected
econ_items = search_items(query=query, time=time, rows=2000)
regulation_items = search_items(query=query, time=time, rows=2000)

# Provide facet names, and items for each facet in first argument.
# Second argument is the name of the project.
new_project = Project.from_search_results(
        {
            'strangle+economy': econ_items,
            'strangle+regulation': regulation_items
        },
        'Strangle instances'
    )

# sync project to MongoDB
new_project.save()
```

## Loading IATV data into metacorps from file system blobs

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
