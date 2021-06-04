import traceback

import flask

import efficient_rhythms

from . import app
from . import er_handler
from . import forms
from . import globals


@app.route("/", methods=("GET", "POST"))
def submit():
    errors = []
    ogg_path = None
    form = forms.ERForm()
    # there is a dict of field names/values in form.data
    # NB it contains "csrf_token" and possibly other things
    if form.validate_on_submit():
        errors.clear()
        try:
            ogg_path = er_handler.make_music(form)
        except efficient_rhythms.er_exceptions.ErMakeException as exc:  # TODO handle build errors
            exc_str = traceback.format_exc()
            errors.append(exc_str)
        else:
            if ogg_path is None:
                errors.append(
                    "Midi file is empty! Nothing to write. "
                    "(Check your settings and try again.)"
                )
        return flask.render_template(
            "form.jinja",
            form=form,
            attr_dict=globals.ATTR_DICT,
            max_priority_dict=globals.MAX_PRIORITY_DICT,
            categories=globals.CATEGORIES,
            errors=errors,
            ogg_path=ogg_path,
        )
        return flask.redirect("/")
    return flask.render_template(
        "form.jinja",
        form=form,
        attr_dict=globals.ATTR_DICT,
        max_priority_dict=globals.MAX_PRIORITY_DICT,
        categories=globals.CATEGORIES,
        errors=errors,
        ogg_path=ogg_path,
    )


import time

from jinja2 import Environment
from jinja2.loaders import PackageLoader


@app.route("/yield")
def index():
    def inner():
        for x in range(100):
            time.sleep(1)
            yield "%s<br/>\n" % x

    env = Environment(loader=PackageLoader("er_web"))
    tmpl = env.get_template("result.html")
    return flask.Response(tmpl.generate(result=inner()))
