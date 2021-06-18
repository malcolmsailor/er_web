import os
import tempfile

import wtforms

import efficient_rhythms


from .midi_to_audio import midi_to_audio
from . import globals_

TEMP_DIR = os.path.join(
    os.path.dirname((os.path.realpath(__file__))), "static/temp_files"
)


def init_temp_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    # TODO delete old files


def temp_path(suffix):
    return tempfile.mkstemp(
        suffix=suffix,
        dir=TEMP_DIR,
    )[1]


def ogg_support():
    # All browsers support mp3 so for now I am just returning False always.
    # Perhaps to-do eventually.
    return False
    # if "safari" in flask.request.user_agent.browser.lower():
    #     return False
    # return True


def make_music(form):
    init_temp_dir()
    user_settings = {}
    for field in form:
        if field.id in ("submit", "csrf_token"):
            continue
        try:
            user_settings[field.id] = field.validated_data
        except AttributeError:
            if isinstance(field, (wtforms.SelectField, wtforms.BooleanField)):
                user_settings[field.id] = field.data
            else:
                raise
    user_settings["timeout"] = globals_.TIMEOUT
    settings = efficient_rhythms.preprocess_settings(user_settings)
    try:
        pattern = efficient_rhythms.make_super_pattern(settings)
        temp_mid = temp_path(".mid")

        audio_format = ".mp3" if not ogg_support() else ".ogg"
        non_empty = efficient_rhythms.write_er_midi(settings, pattern, temp_mid)
    except Exception as exc:
        exc.seed = settings.seed
        raise exc
    if non_empty:
        temp_audio = temp_path(audio_format)
        midi_to_audio(temp_mid, temp_audio)
    if non_empty:
        return (
            settings.seed,
            os.path.join("temp_files", os.path.basename(temp_mid)),
            os.path.join("temp_files", os.path.basename(temp_audio)),
        )
    return settings.seed, None, None
