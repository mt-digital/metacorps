from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, BooleanField
from flask_mongoengine import MongoEngine

app = Flask(__name__)

app.config.update(
    dict(
        SECRET_KEY='dev key',
        MONGODB_SETTINGS={'db': 'metacorps'}
    )
)

db = MongoEngine(app)

from app import models


@app.route('/')
def hello():
    projects = models.IatvProject.objects
    return render_template('index.html', projects=projects)


@app.route('/projects/<project_id>')
def project(project_id):

    project = models.IatvProject.objects.get(pk=project_id)
    facets = project.facets

    return render_template('project.html',
                           facets=facets,
                           project=project)


@app.route('/projects/<project_id>/facets/<facet_word>')
def facet(project_id, facet_word):

    project = models.IatvProject.objects.get(pk=project_id)
    facet = [f for f in project.facets if facet_word == f['word']][0]

    return render_template('facet.html',
                           project=project, facet=facet)


@app.route('/projects/<project_id>/facets/<facet_word>/instances/<int:instance_idx>')
def edit_instance(project_id, facet_word, instance_idx):

    project = models.IatvProject.objects.get(pk=project_id)
    facet = [f for f in project.facets if facet_word == f['word']][0]

    instance = facet.instances[instance_idx]

    form = EditInstanceForm(
        conceptual_metaphor=instance['conceptual_metaphor'],
        objects=instance['objects'],
        subjects=instance['subjects'],
        active_passive=instance['active_passive'],
        notes=instance['description']
    )

    if form.validate_on_submit():
        pass
    else:
        pass

    return render_template('edit_facet.html', form=form,
                           project=project, facet=facet,
                           instance_idx=instance_idx, instance=instance)


class EditInstanceForm(FlaskForm):

    figurative = BooleanField()
    include = BooleanField()
    conceptual_metaphor = TextField(u'Conceptual metaphor')
    objects = TextField(u'Object(s)')
    subjects = TextField(u'Subject(s)')
    active_passive = TextField(u'Active or passive')
    notes = TextAreaField(u'Notes')
