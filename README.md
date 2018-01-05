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

The script [`make_tables.py`](/make_tables.py) creates and saves
LaTeX tables 1-3 as found in the paper. Just run `python make_tables.py`.
That script attempts to save the model fits for each year to file as
`fits{year}.pickle`, e.g. `fits2012.pickle`. Be careful to remove this 
checkpoint if you have updated the data.

This script fetches the data from pre-made csv's hosted on the metacorps
site. These CSV's are created using the same `get_project_data_frame`
function used to load the data from the web in `make_tables.py`. We simply
pass the year of interest and the current version of `get_project_data_frame`
will build the Metacorps project name for lookup in MongoDB. A future version
will not have this convenience, one will just have to pass the full
project name. Projects can have specialized functions that do automatic name
generation on top of this base functionality. Another upcoming change
will be addition of the ability to export all rows, both metaphor and not,
for review by the general public in csv format.

```
viomet_2016 = get_project_data_frame(2016)
viomet_2016.to_csv('viomet-2016-snapshot-project-df.csv', 
                   header=True, index=False, na_rep=None)
```

There are Jupyter Notebooks in the [`notebooks`](/notebooks) directory. 
They need to be updated at this time.

**Another thing to explain or update: frequencies are calculated using both
the CSV data and MongoDB data. How does this work? A CSV of the episode
counts with all relevant metadata should be made for final Jan 15 release.
Note this will also remove need for config file.**

**Separate viomet project from Metacorps? Yes, at least partly. It's OK to
make extensive use of Metacorps, should have separate releases of Mc, iatv,
and reproduce-viomet.**

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
