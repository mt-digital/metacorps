from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField


app = Flask(__name__)

app.config.update(dict(SECRET_KEY='dev key'))

PROJECTS = [
    {
        'id': '1',
        'name': 'Journal of American Mathematics; Embodied Metaphors'
    },
    {
        'id': '2',
        'name': 'Violent metaphor in Cable News'
    }
]


@app.route('/')
def hello():
    return render_template('index.html', projects=PROJECTS)

FACETS = [
    {
        'word': 'attack',
        'total': '395',
        'need_review': '29',
        'id': '1'
    },
    {
        'id': '2',
        'word': 'hit',
        'total': '256',
        'need_review': '109'
    }
]


@app.route('/projects/<project_id>')
def project(project_id):

    project = [p for p in PROJECTS if p['id'] == project_id][0]

    return render_template('project.html',
                           facets=FACETS,
                           project=project)


FACET_INSTANCES = [
    {
        'context': 'in the interview the lawyer was attacked from the left and right',
        'conceptual_metaphor': 'an interview is a physical fight',
        'object(s)': 'a lawyer',
        'subject(s)': 'the interviewers',
        'notes': 'This was the first of four interviews by the public who had identified themselves by their political preference',
        'active/passive': 'passive',
        'facet_id': '1',
        'id': '1'
    },
    {
        'context': 'Obama has never taken a punch',
        'conceptual_metaphor': 'a debate participant is a fighter',
        'object(s)': 'not clear',
        'subject(s)': 'Barack Obama',
        'notes': 'Spoken by Sean Hannity and his guest',
        'active/passive': 'active',
        'facet_id': '1',
        'id': '2'
    },
    {
        'context': 'in the interview the lawyer was attacked from the left and right',
        'conceptual_metaphor': 'an interview is a physical fight',
        'object(s)': 'a lawyer',
        'subject(s)': 'the interviewers',
        'notes': 'This was the first of four interviews by the public who had identified themselves by their political preference',
        'active/passive': 'passive',
        'facet_id': '2',
        'id': '3'
    },
    {
        'context': 'Obama has never taken a punch',
        'conceptual_metaphor': 'a debate participant is a fighter',
        'object(s)': 'not clear',
        'subject(s)': 'Barack Obama',
        'notes': 'Spoken by Sean Hannity and his guest',
        'active/passive': 'active',
        'facet_id': '2',
        'id': '4'
    }
]


@app.route('/projects/<project_id>/facets/<facet_id>')
def facet(project_id, facet_id):

    project = [p for p in PROJECTS if p['id'] == project_id][0]
    facet = [f for f in FACETS if f['id'] == facet_id][0]
    facet_instances = [i for i in FACET_INSTANCES if i['facet_id'] == facet_id]

    return render_template('facet.html',
                           project=project, facet=facet,
                           facet_instances=facet_instances)


@app.route('/projects/<project_id>/facets/<facet_id>/instances/<instance_id>')
def edit_instance(project_id, facet_id, instance_id):

    project = [p for p in PROJECTS if p['id'] == project_id][0]
    facet = [f for f in FACETS if f['id'] == facet_id][0]

    instance = [
        inst for inst in FACET_INSTANCES if inst['id'] == facet_id
    ][0]

    form = EditInstanceForm(
        conceptual_metaphor=instance['conceptual_metaphor'],
        objects=instance['object(s)'],
        subjects=instance['subject(s)'],
        active_passive=instance['active/passive'],
        notes=instance['notes']
    )

    if form.validate_on_submit():
        pass
    else:
        pass

    return render_template('edit_facet.html', form=form,
                           project=project, facet=facet, instance=instance)


class EditInstanceForm(FlaskForm):

    conceptual_metaphor = TextField(u'Conceptual metaphor')
    objects = TextField(u'Object(s)')
    subjects = TextField(u'Subject(s)')
    active_passive = TextField(u'Active or passive')
    notes = TextAreaField(u'Notes')
