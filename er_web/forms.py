import collections

import wtforms
from flask_wtf import FlaskForm

import efficient_rhythms

from . import add_fields, process_docs


class ERForm(FlaskForm):
    submit = wtforms.SubmitField("Submit")

    def __init__(self, request_args):
        super().__init__()
        for field_name, value in request_args.items():
            # # we need to parse boolean args; others seem to be ok as strings
            if value in ("y", "n"):
                # breakpoint()
                value = value == "y"
            try:
                field = getattr(self, field_name)
                field.data = value
            except AttributeError:
                # occurs if field_name is a typo etc.
                # TODO print error message
                pass


add_fields.add_fields_to_form(
    efficient_rhythms.ERSettings,
    ERForm,
)

process_docs.add_links()
