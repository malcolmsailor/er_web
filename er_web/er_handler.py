import os
import tempfile

import efficient_rhythms


from .midi_to_mp4 import midi_to_mp4

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


def make_music(form):
    init_temp_dir()
    user_settings = {}
    for field in form:
        try:
            user_settings[field.id] = field.validated_data
        except AttributeError:
            pass
    # user_settings = form.data.copy()
    # del user_settings["submit"]
    # del user_settings["csrf_token"]
    settings = efficient_rhythms.preprocess_settings(user_settings)
    pattern = efficient_rhythms.make_super_pattern(settings)
    temp_mid = temp_path(".mid")
    non_empty = efficient_rhythms.write_er_midi(settings, pattern, temp_mid)
    if non_empty:
        temp_m4a = temp_path(".m4a")
        midi_to_mp4(temp_mid, temp_m4a)
    if non_empty:
        return os.path.join("temp_files", os.path.basename(temp_m4a))
    return None
