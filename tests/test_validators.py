from numbers import Number
import typing
from typing import List, Optional, Sequence, Tuple, Union
from efficient_rhythms.er_types.types_ import Voice

import wtforms
import numpy as np

import er_web
import er_web.validators as validators
import er_web.forms as forms

from efficient_rhythms.er_types import (
    Density,
    DensityOrQuantity,
    ItemOrSequence,
    Metron,
    PerVoiceSequence,
    PerVoiceSuperSequence,
    JustPitch,
    TemperedPitch,
    Pitch,
    SuperSequence,
    Tempo,
    VoiceRanges,
)

from fixtures import client


# # TODO update this test
# def process_er_constants():
#     items = ("OCTAVE0 * A", "-FIFTH", "MAJOR_SCALE+7")
#     try:
#         for s in items:
#             validators.process_er_constants(s)
#     except:  # pylint: disable=bare-except
#         import sys
#         import traceback

#         exc_type, exc_value, exc_traceback = sys.exc_info()
#         traceback.print_exception(
#             exc_type, exc_value, exc_traceback, file=sys.stdout
#         )
#         breakpoint()


def test_sequence_or_optional_sequence():
    yes = (
        list,
        tuple,
        Tuple[int, int],
        Sequence[bool],
        List,
        List[bool],
        Union[None, Sequence[int]],
        Union[List, None],
        ItemOrSequence,
        # OptItemOrSequence,
        # OptPerVoiceSequence,
        # OptPerVoiceSuperSequence,
        PerVoiceSequence,
        PerVoiceSuperSequence,
        Optional[PerVoiceSequence[int]],
        Sequence[Pitch],
        SuperSequence[Pitch],
        VoiceRanges,
    )
    no = (
        int,
        Union[None, int],
        Union[int, Sequence[int]],
        Union[bool, int],
        Union[None, Sequence[int], int],
        Metron,
        DensityOrQuantity,
        Pitch,
        Tempo,
    )
    for type_hint in yes:
        assert validators.sequence_or_optional_sequence(type_hint)
    for type_hint in no:
        assert not validators.sequence_or_optional_sequence(type_hint)


def test_value_validation():
    # func_name, args, succeed, fail
    tests = [
        ("min_", (2,), (2,), (1,)),
        ("max_", (2,), (2,), (3,)),
        ("open_min", (2,), (2.1,), (2,)),
        ("open_max", (2,), (1.9,), (2,)),
        ("int_min", (2,), (2, 1.0), (1,)),
        ("int_max", (2,), (2, 3.0), (3,)),
        ("float_min", (2.0,), (2.0, 1), (1.0,)),
        ("float_max", (2.0,), (2.0, 3), (3.0,)),
    ]
    for fname, args, succeed, fail in tests:
        f = getattr(validators, fname)
        for x in succeed:
            f(x, *args)
        for x in fail:
            try:
                f(x, *args)
            except wtforms.validators.ValidationError:
                pass
            else:
                raise AssertionError("Test should have failed")


class DummyField:
    def __init__(self, data):
        self.data = data


def test_type_validation():
    to_pass = [
        # (str, "foo"),
        # (Metron, "0.3"),
        # (Metron, "15"),
        # (Pitch, "0.3"),
        # (Pitch, "15"),
        # (JustPitch, "0.3"),
        # (TemperedPitch, "15"),
        # (Tuple[int, int], "(2, 3)"),
        # (Number, "D"),
        # (Number, "D#"),
        # (Number, "D_SHARP"),
        # (Number, "Db"),
        # (int, "SECOND"),
        # (bool, "True"),
        # (Union[None, Sequence[Number]], "0"),
        # (Union[bool, Sequence[bool]], "True, False, True"),
        # (Union[None, Tuple[int]], ""),
        # (Union[None, Tuple[int]], "(2,)"),
        # (Union[None, Tuple[int]], "2,"),
        # (Union[None, Tuple[int]], "2, "),
        # (Union[None, Tuple[int]], " 2, 3"),
        # (Union[None, Tuple[int]], "None"),
        # (Union[None, Sequence[Number]], "(F, A, C)"),
        # (Union[None, Sequence[Number]], "F, A, C"),
        # (Union[None, Sequence[Number]], "F#, A, Cb"),
        # (
        #     Union[Number, np.ndarray, Sequence[Number]],
        #     "MAJOR_TRIAD",
        # ),
        # (
        #     Sequence[Union[np.ndarray, Sequence[Number]]],
        #     "[NATURAL_MINOR_SCALE]",
        # ),
        # (
        #     Sequence[Union[np.ndarray, Sequence[Number]]],
        #     "NATURAL_MINOR_SCALE",
        # ),
        # (
        #     Sequence[Number],
        #     "(OCTAVE,)",
        # ),
        # (
        #     Sequence[Number],
        #     "OCTAVE",
        # ),
        # (
        #     Sequence[Union[np.ndarray, Sequence[Number]]],
        #     "(MAJOR_TRIAD, MINOR_TRIAD)",
        # ),
        # (ItemOrSequence, "4"),
        # (ItemOrSequence, "[4, 5]"),
        # (ItemOrSequence[Pitch], "3.4"),
        # (Optional[ItemOrSequence[Pitch]], ""),
        # (Optional[ItemOrSequence[Pitch]], "3.4"),
        # (SuperSequence[Pitch], "MAJOR_SCALE"),
        # (PerVoiceSequence[Pitch], "6"),
        # (PerVoiceSuperSequence[Pitch], "[MAJOR_SCALE]"),
        # (SuperSequence[Pitch], "[MAJOR_SCALE]"),
        # (VoiceRanges, "CONTIGUOUS_OCTAVES * OCTAVE3 * C"),
        # (VoiceRanges, "((16.0, 32.0), (32.0, 64.0), (64.0, 128.0), (128.0, 256.0), (256.0, 512.0), (512.0, 1024.0), (1024.0, 2048.0))"),
        (VoiceRanges, "((OCTAVE0 * A, OCTAVE8 * C),)"),
    ]
    to_fail = [
        (Pitch, "foo"),
        (TemperedPitch, "0.3"),
        (JustPitch, "15"),
        (Tuple[int, int], "(foo, 3)"),
        (Union[Number, Sequence[Number]], "foo"),
        (float, "SECOND"),
        (
            Union[
                Number,
                Sequence[Number],
            ],
            "foo",
        ),
        (ItemOrSequence[Pitch], "foo"),
        (ItemOrSequence[Pitch], '[3, 4, "foo"]'),
        (
            Sequence[Union[np.ndarray, Sequence[Number]]],
            "[[  16.   32.] [  24.   48.]]",
        ),
        # NB the next text of VoiceRanges will *pass* because we remove "excess"
        #   parentheses from sequences of len(1) in validators.validate_field()
        # (VoiceRanges, "(((16.0, 32.0), (32.0, 64.0), (64.0, 128.0), (128.0, 256.0), (256.0, 512.0), (512.0, 1024.0), (1024.0, 2048.0)),)")
    ]
    to_pass_with_val_dict = [
        (
            Sequence[Union[np.ndarray, Sequence[Number]]],
            {"min_": (0,)},
            "[NATURAL_MINOR_SCALE]",
        ),
    ]
    empty_val_dict = {}

    for type_hint, value in to_pass:
        field = DummyField(value)
        breakpoint()
        validators.validate_field(type_hint, empty_val_dict, None, field)
    for type_hint, val_dict, value in to_pass_with_val_dict:
        field = DummyField(value)
        validators.validate_field(type_hint, val_dict, None, field)
    for type_hint, value in to_fail:
        field = DummyField(value)
        try:
            validators.validate_field(type_hint, empty_val_dict, None, field)
        except wtforms.validators.ValidationError:
            continue
        else:
            raise AssertionError("There should have been a validation error")


def test_form_validation(client):
    with er_web.app.test_request_context():
        form = forms.ERForm({})
        form.validate()
        for field, error in form.errors.items():
            print(f"Validation error: {field}: {error}")
            raise AssertionError(f"See printed validation errors")


if __name__ == "__main__":
    test_type_validation()
