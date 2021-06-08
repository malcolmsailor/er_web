import efficient_rhythms
import malsynth
from .constants import ER_CONSTANTS

ATTR_DICT = {}
MAX_PRIORITY_DICT = {}
IGNORED_CATEGORIES = (
    "midi",
    "shell_only",
    "tuning",
)
CATEGORIES = tuple(
    c for c in efficient_rhythms.CATEGORIES if c not in IGNORED_CATEGORIES
)

DEFAULT_FIELD_VALUES = {}

WEB_DEFAULTS = {
    "choirs": [16, 21, 15],
    # eventually I would like to migrate some of these values over to the script
    "num_harmonies": 4,
    "max_interval": 4,
    "force_foot_in_bass": "global_first_beat",
    "force_chord_tone": "global_first_note",
    "pattern_len": 2,
    "harmony_len": 4,
    "foot_pcs": [0, 5, 10, 3],
    "preserve_foot_in_bass": "lowest",
    "scales": "[NATURAL_MINOR_SCALE]",
    "chords": "[MINOR_TRIAD]",
    "randomly_distribute_between_choirs": True,
    "length_choir_segments": 2,
    "max_consec_seg_from_same_choir": 1,
    "onset_density": 0.65,
    "dur_density": 0.65,
    "voice_lead_chord_tones": True,
    "tempo": 144,
}

VAL_DICTS = {
    "choirs": {"min_": (min(malsynth.synths),), "max_": (max(malsynth.synths),)}
}


synths = []
for i, synth_class in malsynth.synths.items():
    synths.append(f"- {i}: {synth_class.__name__}")

CHOIR_DOC = """Sequence of ints.

Each integer selects one of the following elementary synth presets:

""" + "\n".join(
    synths
)


DOCS = {
    "choirs": CHOIR_DOC,
}
