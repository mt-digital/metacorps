from .app import db

from datetime import datetime


class IatvDocument(db.Document):

    document_data = db.StringField(required=True)
    air_datetime = db.DateTimeField()
    network = db.StringField()
    program_name = db.StringField()
    raw_srt = db.StringField(required=True)

    meta = {
        'indexes': [
            {
                'fields': ['$document_data'],
                'default_language': 'english'
            }
        ]
    }


class IatvCorpus(db.Document):

    name = db.StringField()
    documents = db.ListField(db.ReferenceField(IatvDocument))


class Instance(db.EmbeddedDocument):

    text = db.StringField(required=True)
    source_id = db.ObjectIdField(required=True)

    figurative = db.BooleanField()
    include = db.BooleanField(default=True)

    conceptual_metaphor = db.StringField(default='')
    objects = db.StringField(default='')
    subjects = db.StringField(default='')
    active_passive = db.StringField(default='')
    description = db.StringField(default='')

    completed = db.BooleanField(default=False)


class Facet(db.EmbeddedDocument):

    instances = db.ListField(db.EmbeddedDocumentField(Instance))
    word = db.StringField()
    total_count = db.IntField(default=0)
    number_reviewed = db.IntField(default=0)


class IatvProject(db.Document):

    corpus = db.ReferenceField(IatvCorpus)
    name = db.StringField()
    created = db.DateTimeField(default=datetime.now)
    facets = db.ListField(db.EmbeddedDocumentField(Facet))
    last_modified = db.DateTimeField(default=datetime.now)
