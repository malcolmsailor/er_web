from dataclasses import dataclass
from numbers import Number
import types
from typing import Optional, Sequence, Tuple, Union

import numpy as np

import efficient_rhythms
from efficient_rhythms.er_types import (
    Density,
    DensityOrQuantity,
    ItemOrSequence,
    Metron,
    PerVoiceSequence,
    PerVoiceSuperSequence,
    Pitch,
    PitchClass,
    SuperSequence,
    Tempo,
    VoiceRanges,
)
import malsynth

TIMEOUT = 10.0

ATTR_DICT = {}
MAX_PRIORITY_DICT = {}
IGNORED_CATEGORIES = (
    "midi",
    "shell_only",
)
CATEGORIES = tuple(
    c for c in efficient_rhythms.CATEGORIES if c not in IGNORED_CATEGORIES
)

BASIC_FIELDS = (
    "onset_density",
    "num_voices",
    "tempo",
)

FIELD_NAME_ABBREVS = {
    "num": "number of",
    "len": "length",
    "pcs": "pitch-classes",
    "dur": "duration",
    "consec": "consecutive",
    "seg": "segments",
    "cont": "continuous",
    "var": "variation",
    "reps": "repetitions",
    "vl": "voice leading",
}
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
    "consonance_treatment": "none",
    "consonances": "0, 3, 4, 5, 7, 8, 9",
    # TODO hard_bounds default is temporary (maybe), if we get it automatically
    # it looks something like "(('OCTAVE0 * A', 'OCTAVE8 * C'),)", and these
    # internal strings cause problems
    "hard_bounds": "((OCTAVE0 * A, OCTAVE8 * C),)",
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

CONSTANT_GROUP_LABELS = types.MappingProxyType(
    {
        "pitch_class": "Pitch classes",
        "specific_interval": "Specific intervals",
        "generic_interval": "Generic intervals",
        "three_chord": "Three-note chords",
        "four_chord": "Four-note chords",
        "three_position": "Three-note chord positions",
        "seven_scale": "Seven-note scales",
        "five_scale": "Five-note scales",
        "six_scale": "Six-note scales",
        "eight_scale": "Eight-note scales",
        "nine_scale": "Nine-note scales",
        "octave": "Octaves",
        "voice_range": "Voice ranges",
    }
)

CONSTANT_SUPER_GROUPS = types.MappingProxyType(
    {
        "chord": ("three_chord", "four_chord"),
        "scale": (
            "seven_scale",
            "five_scale",
            "six_scale",
            "eight_scale",
            "nine_scale",
        ),
    }
)

TEMP_CONSTANT_GROUPS = {
    "pitch_class": (
        "C",
        "D",
        "E",
        "F",
        "G",
        "A",
        "B",
        "Cbb",
        "Dbb",
        "Ebb",
        "Fbb",
        "Gbb",
        "Abb",
        "Bbb",
        "Cb",
        "Db",
        "Eb",
        "Fb",
        "Gb",
        "Ab",
        "Bb",
        "C_SHARP",
        "D_SHARP",
        "E_SHARP",
        "F_SHARP",
        "G_SHARP",
        "A_SHARP",
        "B_SHARP",
        "C_SHARP_SHARP",
        "D_SHARP_SHARP",
        "E_SHARP_SHARP",
        "F_SHARP_SHARP",
        "G_SHARP_SHARP",
        "A_SHARP_SHARP",
        "B_SHARP_SHARP",
    ),
    "specific_interval": (
        "UNISON",
        "MINOR_2ND",
        "MAJOR_2ND",
        "MINOR_3RD",
        "MAJOR_3RD",
        "PERFECT_4TH",
        "DIMINISHED_5TH",
        "PERFECT_5TH",
        "AUGMENTED_5TH",
        "MINOR_6TH",
        "MAJOR_6TH",
        "MINOR_7TH",
        "MAJOR_7TH",
        "OCTAVE",
        "MINOR_9TH",
        "MAJOR_9TH",
        "MINOR_10TH",
        "MAJOR_10TH",
    ),
    "generic_interval": (
        "GENERIC_UNISON",
        "SECOND",
        "THIRD",
        "FOURTH",
        "FIFTH",
        "SIXTH",
        "SEVENTH",
        "GENERIC_OCTAVE",
    ),
    "three_chord": (
        "MAJOR_TRIAD",
        "MINOR_TRIAD",
        "DIMINISHED_TRIAD",
        "AUGMENTED_TRIAD",
        "HALF_DIMINISHED_NO5",
        "HALF_DIMINISHED_NO3",
        "DOMINANT_7TH_NO5",
        "DOMINANT_7TH_NO3",
        "MAJOR_7TH_NO5",
        "MAJOR_7TH_NO3",
        "MINOR_7TH_NO5",
        "MINOR_7TH_NO3",
    ),
    "four_chord": (
        "HALF_DIMINISHED_CHORD",
        "DOMINANT_7TH_CHORD",
        "MAJOR_7TH_CHORD",
        "MINOR_7TH_CHORD",
    ),
    "three_position": (
        "MAJOR_53",
        "MAJOR_63",
        "MAJOR_64",
        "MINOR_53",
        "MINOR_63",
        "MINOR_64",
        "MAJOR_53_OPEN",
        "MAJOR_63_OPEN",
        "MAJOR_64_OPEN",
        "MINOR_53_OPEN",
        "MINOR_63_OPEN",
        "MINOR_64_OPEN",
    ),
    "seven_scale": (
        "DIATONIC_SCALE",
        "MAJOR_SCALE",
        "NATURAL_MINOR_SCALE",
        "IONIAN",
        "DORIAN",
        "PHRYGIAN",
        "LYDIAN",
        "MIXOLYDIAN",
        "AEOLIAN",
        "LOCRIAN",
    ),
    "five_scale": ("PENTATONIC_SCALE",),
    "six_scale": (
        "HEXACHORD_MAJOR",
        "HEXACHORD_MINOR",
        "WHOLE_TONE",
        "HEXATONIC01",
        "HEXATONIC03",
    ),
    "eight_scale": (
        "OCTATONIC01",
        "OCTATONIC02",
    ),
    "nine_scale": (
        "ENNEATONIC012",
        "ENNEATONIC013",
        "ENNEATONIC023",
    ),
    "octave": (
        "OCTAVE0",
        "OCTAVE1",
        "OCTAVE2",
        "OCTAVE3",
        "OCTAVE4",
        "OCTAVE5",
        "OCTAVE6",
        "OCTAVE7",
        "OCTAVE8",
    ),
    "voice_range": (
        "CONTIGUOUS_OCTAVES",
        "CONTIGUOUS_4THS",
        "CONTIGUOUS_5THS",
        "CONTIGUOUS_12THS",
        "CONTIGUOUS_15THS",
        "AUTHENTIC_OCTAVES",
        "AUTHENTIC_5THS",
        "AUTHENTIC_12THS",
        "AUTHENTIC_15THS",
        "PLAGAL_OCTAVES",
        "PLAGAL_5THS",
    ),
}


def get_constant_groups():
    out = {}
    for group, constants in TEMP_CONSTANT_GROUPS.items():
        out[group] = tuple(
            efficient_rhythms.CONSTANTS_BY_NAME[constant]
            for constant in constants
        )
    return out


CONSTANT_GROUPS = types.MappingProxyType(get_constant_groups())

# TODO update
TYPING_STRINGS = {
    # bool: not necessary
    int: "An integer",
    float: "A number",
    Number: "A number",
    Sequence[int]: "A sequence of integers separated by commas",
    Sequence[Number]: "A sequence of numbers separated by commas",
    Union[float, int, Sequence[Union[float, int]]]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    Union[float, Sequence[float]]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    # TODO what if the user wants a sequence of length 1?
    Union[None, int]: "Blank, or an integer",
    Union[None, Number]: "Blank, or a number",
    Union[None, Sequence[Number]]: (
        "Blank, or a sequence of numbers separated by commas"
    ),
    Union[None, Sequence[int]]: (
        "Blank, or a sequence of integers separated by commas"
    ),
    Union[None, Tuple[int, int]]: (
        "Blank, or two numbers separated by a comma"
    ),
    Union[int, Sequence[int]]: (
        "An integer, or a sequence of integers separated by commas"
    ),
    Union[Number, Sequence[Number]]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    Union[None, int, Sequence[int]]: (
        "Blank, an integer, or a sequence of integers separated by commas"
    ),
    Union[None, Number, Sequence[Number]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    Union[str, int, Sequence[Union[str, int]]]: (
        "A string, an integer, or a sequence of strings or integers "
        "separated by commas"
    ),
    Union[Sequence[Tuple[Number, Number]], np.ndarray,]: (
        "A sequence of two-tuples of numbers (e.g., '(1, 2)') separated by "
        "commas"
    ),
    Sequence[Union[np.ndarray, Sequence[Number]]]: (
        "A sequence of sequences of numbers (e.g., '(0, 3, 7)'), separated by "
        "commas"
    ),
    Sequence[Tuple[Number, Number]]: (
        "A sequence of two-tuples of numbers (e.g., '(1, 2)') separated by "
        "commas"
    ),
    Union[bool, Sequence[bool]]: (
        "A boolean (either 'True' or 'False'), or a sequence of booleans "
        "separated by commas"
    ),
    Union[bool, Sequence[Sequence[int]]]: (
        "A boolean (either 'True' or 'False'), or a sequence of sequences of "
        "integers"
    ),
    Union[None, Number, Sequence[Union[Number, Sequence[Number]]],]: (
        "Blank, or a number, or a sequence of numbers, or a sequence of "
        "sequences of numbers"
    ),
    Union[int, Sequence[Union[int, Sequence[int]]]]: (
        "An integer, or a sequence of integers, or a sequence of sequences of "
        "integers"
    ),
    Tuple[Number, Number]: ("Two numbers separated by a comma"),
    Sequence[Union[Number, Sequence[Number]]]: (
        "A sequence of numbers, or a sequence of sequences of numbers"
    ),
    Union[None, int, Sequence[Union[int, Sequence[int]]]]: (
        "Blank, or an integer, or a sequence of integers, or a sequence of "
        "sequences of integers"
    ),
    Union[None, Sequence[Union[Number, Sequence[Number]]],]: (
        "Blank, or a sequence of numbers, or a sequence of sequences of numbers"
    ),
    # custom types
    Optional[ItemOrSequence[Pitch]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    Optional[ItemOrSequence[PitchClass]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    Optional[ItemOrSequence[Metron]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    Optional[ItemOrSequence[Tempo]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    SuperSequence[Pitch]: (
        "A sequence of sequences of numbers (e.g., '(0, 3, 7)'), separated by "
        "commas"
    ),
    ItemOrSequence[Metron]: (
        "A number, or a sequence of numbers separated by commas"
    ),
    Optional[PerVoiceSequence[Metron]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
    Optional[PerVoiceSequence[Pitch]]: (
        "Blank, a number, or a sequence of numbers separated by commas"
    ),
}
# TODO check for missing custom types

# TODO deal with force_parallel_motion type


# @dataclass
# class HarmonyPreset:
#     num_harmonies: int
#     foot_pcs: Optional[ItemOrSequence[PitchClass]]
#     scales: SuperSequence[Pitch]
#     chords: SuperSequence[Pitch]


# HARMONY_PRESETS = (
#     HarmonyPreset(4, (0, 5, 10, 3), "NATURAL_MINOR_SCALE", "MINOR_TRIAD"),
#     HarmonyPreset(
#         4,
#         ("C", "G", "A", "F"),
#         ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
#         ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),
#     ),
#     HarmonyPreset(
#         4,
#         ("D",),
#         ("MAJOR_7TH_NO5", "DOMINANT_7TH_NO3", "MAJOR_64", "MAJOR_63"),
#         ("MAJOR_SCALE", "MIXOLYDIAN", "DORIAN", "AEOLIAN"),
#     ),
# )

HARMONY_PRESET_TUPLES = (
    # num_harmonies, foot_pcs, scales, chords
    ("4", "0, 5, 10, 3", "NATURAL_MINOR_SCALE", "MINOR_TRIAD"),
    (
        "4",
        "C, G, A, F",
        "MAJOR_SCALE, MIXOLYDIAN, AEOLIAN, LYDIAN",
        "MAJOR_TRIAD, MAJOR_TRIAD, MINOR_TRIAD, MAJOR_TRIAD",
    ),
    (
        "4",
        "D",
        "MAJOR_SCALE, MIXOLYDIAN, DORIAN, AEOLIAN",
        "MAJOR_7TH_NO5, DOMINANT_7TH_NO3, MAJOR_64, MAJOR_63",
    ),
)

HARMONY_PRESETS = tuple(
    {"num_harmonies": a, "foot_pcs": b, "scales": c, "chords": d}
    for a, b, c, d in HARMONY_PRESET_TUPLES
)

if __name__ == "__main__":
    out = []
    for (
        field_name,
        field_args,
    ) in efficient_rhythms.ERSettings.__dataclass_fields__.items():
        if field_args.type not in TYPING_STRINGS and field_args.type not in out:
            print(field_name, field_args.type)
            out.append(field_args.type)
