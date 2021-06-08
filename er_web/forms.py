import collections

import wtforms
from flask_wtf import FlaskForm

import efficient_rhythms

from . import add_fields, process_docs


class ERForm(FlaskForm):
    submit = wtforms.SubmitField("Submit")


add_fields.add_fields_to_form(
    efficient_rhythms.ERSettings,
    ERForm,
)

process_docs.add_links()
