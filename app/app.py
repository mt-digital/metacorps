import re

from datetime import time
from flask import Flask, render_template, redirect, url_for
from flask_mongoengine import MongoEngine
from flask_security import MongoEngineUserDatastore, Security, login_required, logout_user
from flask_wtf import FlaskForm
from numpy import unique
from wtforms import TextField, TextAreaField, BooleanField

from iatv import DOWNLOAD_BASE_URL

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super-secret'

app.config.update(
    dict(
        SECRET_KEY='dev key',
        MONGODB_SETTINGS={'db': 'metacorps'}
    )
)

db = MongoEngine(app)

from app import models

user_datastore = MongoEngineUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)

@app.before_first_request
def create_user():
    user_datastore.create_user(email='mt@yo.org', password='password')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/')
@login_required
def hello():
    projects = models.Project.objects
    return render_template('index.html', projects=projects)


@app.route('/projects/<project_id>')
@login_required
def project(project_id):

    project = models.Project.objects.get(pk=project_id)
    facets = project.facets

    return render_template('project.html',
                           facets=facets,
                           project=project)


@app.route('/projects/<project_id>/facets/<facet_word>')
@login_required
def facet(project_id, facet_word):

    project = models.Project.objects.get(pk=project_id)
    facet = [f for f in project.facets if facet_word == f['word']][0]
    iatv_documents = [
        models.IatvDocument.objects.get(pk=instance.source_id)
        for instance in facet.instances
    ]

    return render_template('facet.html',
                           project=project, facet=facet,
                           iatv_documents=iatv_documents)


@app.route('/projects/<project_id>/facets/<facet_word>/instances/<int:instance_idx>', methods=['GET', 'POST'])
@login_required
def edit_instance(project_id, facet_word, instance_idx):

    project = models.Project.objects.get(pk=project_id)
    facet = [f for f in project.facets if facet_word == f['word']][0]

    instance = facet.instances[instance_idx]
    total_instances = len(facet.instances)

    source_doc = models.IatvDocument.objects.get(pk=instance.source_id)

    srt_text, video_clip_url = _retrieve_iatv_context(instance, source_doc)

    form = EditInstanceForm(
        figurative=instance['figurative'],
        include=instance['include'],
        conceptual_metaphor=instance['conceptual_metaphor'],
        objects=instance['objects'],
        subjects=instance['subjects'],
        active_passive=instance['active_passive'],
        description=instance['description'],
        srt_text=srt_text,
        video_clip_url=video_clip_url
    )

    if form.validate_on_submit():

        cm = form.conceptual_metaphor.data
        fig = form.figurative.data
        inc = form.include.data
        obj = form.objects.data
        subj = form.subjects.data
        ap = form.active_passive.data
        desc = form.description.data

        # if not fig or (cm != '' and fig != '' and obj != '' and subj != '' and
        #                ap != '' and desc != ''):
        #     instance['completed'] = True

        instance['conceptual_metaphor'] = cm
        instance['figurative'] = fig
        instance['include'] = inc
        instance['objects'] = obj
        instance['subjects'] = subj
        instance['active_passive'] = ap
        instance['description'] = desc

        instance.save()

        next_url = url_for(
                'edit_instance', project_id=project_id, facet_word=facet_word,
                instance_idx=instance_idx+1
            )

        return redirect(next_url)

    return render_template('edit_facet.html', form=form,
                           project=project, facet=facet,
                           instance_idx=instance_idx, instance=instance,
                           source_doc=source_doc,
                           total_instances=total_instances,
                           srt_text=srt_text, video_clip_url=video_clip_url)


class EditInstanceForm(FlaskForm):

    figurative = BooleanField()
    include = BooleanField()
    conceptual_metaphor = TextField(u'Conceptual metaphor')
    objects = TextField(u'Object(s)')
    subjects = TextField(u'Subject(s)')
    active_passive = TextField(u'Active or passive')
    description = TextAreaField(u'Description')


def _retrieve_iatv_context(instance, source_doc,
                           num_pad_chars=500):

    raw_srt = source_doc.raw_srt
    short = ' '.join(instance.text.strip().split(' ')[:4])

    find_idx = raw_srt.find(short)

    srt_clip = raw_srt[find_idx - num_pad_chars:find_idx + num_pad_chars]

    time_re = r'\d{2}:\d{2}:\d{2}'
    string_times = unique(re.findall(time_re, srt_clip))

    times = [
        time(*[int(t) for t in time_tuple])
        for time_tuple in [string_time.split(':')
                           for string_time in string_times]
    ]

    start_time = times[0].second//10 * 10
    stop_time = (times[-1].second//10 * 10) + 50

    url = DOWNLOAD_BASE_URL + source_doc.iatv_id + '/' +\
        source_doc.iatv_id + '.mp4?t={}/{}&exact=1&ignore=x.mp4'.format(
            start_time, stop_time
        )

    return (srt_clip, url)
