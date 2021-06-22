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
    succeeded = False
    script_error = seed = None
    error_type = ""
    if form.validate_on_submit():
        try:
            seed, midi_path, audio_path = er_handler.make_music(form)
            succeeded = True
        except efficient_rhythms.TimeoutError as exc:
            script_error = True
            error_type = "timeout"
            seed = exc.seed
        except efficient_rhythms.ErMakeError as exc:
            script_error = str(exc)
            error_type = "make"
            seed = exc.seed
        except efficient_rhythms.ErSettingsError as exc:
            exc_str = str(exc)
            script_error = exc_str.split("\n")
            error_type = "settings"
            # This error is thrown in preprocessing so there is no seed yet
        except Exception as exc:
            seed = exc.seed
            exc_str = traceback.format_exc()
            script_error = exc_str
            error_type = "exception"
    if not succeeded:
        midi_path, audio_path = None, None
    empty = audio_path is None
    return flask.render_template(
        "base.jinja",
        form=form,
        attr_dict=globals_.ATTR_DICT,
        max_priority_dict=globals_.MAX_PRIORITY_DICT,
        categories=globals_.CATEGORIES,
        default_field_values=globals_.DEFAULT_FIELD_VALUES,
        script_error=script_error,
        error_type=error_type,
        empty=empty,
        audio_path=audio_path,
        midi_path=midi_path,
        seed=seed,
    )


# TODO remove
@app.route("/test/")
def test_page():
    return "Hello world"
