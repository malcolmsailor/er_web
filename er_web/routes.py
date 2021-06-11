import traceback

import flask

import efficient_rhythms

from . import app
from . import er_handler
from . import forms
from . import globals_


@app.route("/", methods=("GET", "POST"))
def mainpage():
    form = forms.ERForm(flask.request.args)
    # there is a dict of field names/values in form.data
    # NB it contains "csrf_token" and possibly other things
    succeeded = timeout = False
    script_error = settings_error = None
    if form.validate_on_submit():
        try:
            seed, midi_path, audio_path = er_handler.make_music(form)
            succeeded = True
        except efficient_rhythms.TimeoutError:
            timeout = True
        except efficient_rhythms.ErSettingsError as exc:
            exc_str = str(exc)
            settings_error = exc_str.split("\n")
        except Exception:
            exc_str = traceback.format_exc()
            script_error = exc_str
    if not succeeded:
        seed, midi_path, audio_path = None, None, None
    empty = audio_path is None
    return flask.render_template(
        "base.jinja",
        form=form,
        attr_dict=globals_.ATTR_DICT,
        max_priority_dict=globals_.MAX_PRIORITY_DICT,
        categories=globals_.CATEGORIES,
        default_field_values=globals_.DEFAULT_FIELD_VALUES,
        script_error=script_error,
        settings_error=settings_error,
        empty=empty,
        audio_path=audio_path,
        midi_path=midi_path,
        seed=seed,
        timeout=timeout,
    )


# TODO remove
@app.route("/test/")
def test_page():
    return flask.render_template("test.jinja", items=["foo", "bar"])
