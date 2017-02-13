import requests
import numpy as np
import os

from datetime import datetime
from flask_security import UserMixin, RoleMixin

from .app import db

DOWNLOAD_BASE_URL = 'https://archive.org/download/'


class IatvDocument(db.Document):

    document_data = db.StringField(required=True)
    raw_srt = db.StringField(required=True)
    iatv_id = db.StringField(required=True)
    iatv_url = db.URLField(required=True)

    network = db.StringField()
    program_name = db.StringField()

    # somewhat redundant in case localtime is missing or other issues
    start_localtime = db.DateTimeField()
    start_time = db.DateTimeField()
    stop_time = db.DateTimeField()
    runtime_seconds = db.FloatField()
    utc_offset = db.StringField()

    def download_video(self, download_dir):

        segments = int(np.ceil(self.runtime_seconds / 60.0))

        for i in range(segments):
            start_time = i * 60
            stop_time = (i + 1) * 60
            download_url = DOWNLOAD_BASE_URL + self.iatv_id + '/' +\
                self.iatv_id + '.mp4?t=' + str(start_time) + '/' +\
                str(stop_time) + '&exact=1&ignore=x.mp4'

            res = requests.get(download_url)

            download_path = os.path.join(
                download_dir, '{}_{}.mp4'.format(self.iatv_id, i))

            with open(download_path, 'wb') as handle:
                handle.write(res.content)


class IatvCorpus(db.Document):

    name = db.StringField()
    documents = db.ListField(db.ReferenceField(IatvDocument))


class Instance(db.EmbeddedDocument):

    text = db.StringField(required=True)
    source_id = db.ObjectIdField(required=True)

    figurative = db.BooleanField(default=False)
    include = db.BooleanField(default=False)

    conceptual_metaphor = db.StringField(default='')
    objects = db.StringField(default='')
    subjects = db.StringField(default='')
    active_passive = db.StringField(default='')
    tense = db.StringField(default='')
    description = db.StringField(default='')

    reviewed = db.BooleanField(default=False)

    reference_url = db.URLField()


class Facet(db.Document):

    instances = db.ListField(db.EmbeddedDocumentField(Instance))
    word = db.StringField()
    total_count = db.IntField(default=0)
    number_reviewed = db.IntField(default=0)


# class IatvProject(db.Document):
class Project(db.Document):

    name = db.StringField(required=True)

    # corpus = db.ReferenceField(IatvCorpus)
    created = db.DateTimeField(default=datetime.now)
    facets = db.ListField(db.ReferenceField(Facet))
    last_modified = db.DateTimeField(default=datetime.now)


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])


class Log(db.Document):
    time_posted = db.DateTimeField(default=datetime.now)
    user_email = db.StringField()
    message = db.StringField()
