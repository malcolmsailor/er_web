import numbers
import typing

import numpy as np

import efficient_rhythms
import malsynth

TIMEOUT = 10.0

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
    "choirs": "16, 21, 15",
    # eventually I would like to migrate some of these values over to the script
    "num_harmonies": 4,
    "max_interval": 4,
    "force_foot_in_bass": "global_first_beat",
    "force_chord_tone": "global_first_note",
    "pattern_len": 2,
    "harmony_len": 4,
    "foot_pcs": "0, 5, 10, 3",
    "preserve_foot_in_bass": "lowest",
    "scales": "NATURAL_MINOR_SCALE",
    "chords": "MINOR_TRIAD",
    "randomly_distribute_between_choirs": True,
    "length_choir_segments": 2,
    "max_super_pattern_len": 64,
    "max_consec_seg_from_same_choir": 1,
    "onset_density": 0.65,
    "dur_density": 0.65,
    "voice_lead_chord_tones": True,
    "tempo": 144,
    "consonances": "0, 3, 4, 5, 7, 8, 9",
}

MAX_SEQ_LEN = 16
MAX_SUBSEQ_LEN = 8

VAL_DICTS = {
    "choirs": {
        "min_": (min(malsynth.synths),),
        "max_": (max(malsynth.synths),),
    },
    "num_voices": {"max_": (6,)},
    "num_reps_super_pattern": {"min_": (1,), "max_": (4,)},
    "pattern_len": {"min_": (0.1,), "max_": (32,)},
    "rhythm_len": {"min_": (0.1,), "max_": (32,)},
    "num_harmonies": {"min_": (1,), "max_": (16,)},
    "harmony_len": {"min_": (0.1,), "max_": (32,)},
    "max_super_pattern_len": {"min_": (0,), "max_": (64,)},
    "foot_pcs": {"min_": (0,)},
    "scales": {"min_": (0,), "subseq_max_len": (12,)},
    "chords": {"min_": (0,)},  # TODO verify
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

# TODO update
TYPING_STRINGS = {
    # bool: not necessary
    int: "An integer",
    float: "A number",
    numbers.Number: "A number",
    typing.Sequence[int]: "A sequence of integers separated by commas",
    typing.Sequence[
        numbers.Number
    ]: "A sequence of numbers separated by commas",
    typing.Union[float, int, typing.Sequence[typing.Union[float, int]]]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    typing.Union[float, typing.Sequence[float]]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    # TODO what if the user wants a sequence of length 1?
    typing.Union[None, int]: "Blank, or an integer",
    typing.Union[None, numbers.Number]: "Blank, or a number",
    typing.Union[None, typing.Sequence[numbers.Number]]: (
        "Blank, or a sequence of numbers separated by commas"
    ),
    typing.Union[None, typing.Sequence[int]]: (
        "Blank, or a sequence of integers separated by commas"
    ),
    typing.Union[None, typing.Tuple[int, int]]: (
        "Blank, or two numbers separated by a comma"
    ),
    typing.Union[int, typing.Sequence[int]]: (
        "An integer, or a sequence of integers separated by commas"
    ),
    typing.Union[numbers.Number, typing.Sequence[numbers.Number]]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    typing.Union[None, int, typing.Sequence[int]]: (
        "Blank, an integer, or a sequence of integers separated by commas"
    ),
    typing.Union[None, numbers.Number, typing.Sequence[numbers.Number]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    typing.Union[str, int, typing.Sequence[typing.Union[str, int]]]: (
        "A string, an integer, or a sequence of strings or integers "
        "separated by commas"
    ),
    typing.Union[
        typing.Sequence[typing.Tuple[numbers.Number, numbers.Number]],
        np.ndarray,
    ]: (
        "A sequence of two-tuples of numbers (e.g., '(1, 2)') separated by "
        "commas"
    ),
    typing.Sequence[
        typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
    ]: (
        "A sequence of sequences of numbers (e.g., '(0, 3, 7)'), separated by "
        "commas"
    ),
    typing.Sequence[typing.Tuple[numbers.Number, numbers.Number]]: (
        "A sequence of two-tuples of numbers (e.g., '(1, 2)') separated by "
        "commas"
    ),
    typing.Union[bool, typing.Sequence[bool]]: (
        "A boolean (either 'True' or 'False'), or a sequence of booleans "
        "separated by commas"
    ),
    typing.Union[bool, typing.Sequence[typing.Sequence[int]]]: (
        "A boolean (either 'True' or 'False'), or a sequence of sequences of "
        "integers"
    ),
    typing.Union[
        None,
        numbers.Number,
        typing.Sequence[
            typing.Union[numbers.Number, typing.Sequence[numbers.Number]]
        ],
    ]: (
        "Blank, or a number, or a sequence of numbers, or a sequence of "
        "sequences of numbers"
    ),
    typing.Union[
        int, typing.Sequence[typing.Union[int, typing.Sequence[int]]]
    ]: (
        "An integer, or a sequence of integers, or a sequence of sequences of "
        "integers"
    ),
    typing.Tuple[numbers.Number, numbers.Number]: (
        "Two numbers separated by a comma"
    ),
    typing.Sequence[
        typing.Union[numbers.Number, typing.Sequence[numbers.Number]]
    ]: ("A sequence of numbers, or a sequence of sequences of numbers"),
    typing.Union[
        None, int, typing.Sequence[typing.Union[int, typing.Sequence[int]]]
    ]: (
        "Blank, or an integer, or a sequence of integers, or a sequence of "
        "sequences of integers"
    ),
    typing.Union[
        None,
        typing.Sequence[
            typing.Union[numbers.Number, typing.Sequence[numbers.Number]]
        ],
    ]: (
        "Blank, or a sequence of numbers, or a sequence of sequences of numbers"
    ),
}

# TODO deal with force_parallel_motion type

if __name__ == "__main__":
    out = []
    for (
        field_name,
        field_args,
    ) in efficient_rhythms.ERSettings.__dataclass_fields__.items():
        if field_args.type not in TYPING_STRINGS and field_args.type not in out:
            print(field_name, field_args.type)
            out.append(field_args.type)
