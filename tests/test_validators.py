import numbers
import typing

import wtforms
import numpy as np

import er_web
import er_web.validators as validators
import er_web.forms as forms


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
        typing.Tuple[int, int],
        typing.Sequence[bool],
        typing.List,
        typing.List[bool],
        typing.Union[None, typing.Sequence[int]],
        typing.Union[typing.List, None],
    )
    no = (
        int,
        typing.Union[None, int],
        typing.Union[int, typing.Sequence[int]],
        typing.Union[bool, int],
        typing.Union[None, typing.Sequence[int], int],
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
        (str, "foo"),
        (typing.Tuple[int, int], "(2, 3)"),
        (numbers.Number, "D"),
        (numbers.Number, "D#"),
        (numbers.Number, "D_SHARP"),
        (numbers.Number, "Db"),
        (int, "SECOND"),
        (bool, "True"),
        (typing.Union[None, typing.Sequence[numbers.Number]], "0"),
        (typing.Union[bool, typing.Sequence[bool]], "True, False, True"),
        (typing.Union[None, typing.Tuple[int]], ""),
        (typing.Union[None, typing.Tuple[int]], "(2,)"),
        (typing.Union[None, typing.Tuple[int]], "2,"),
        (typing.Union[None, typing.Tuple[int]], "None"),
        (typing.Union[None, typing.Sequence[numbers.Number]], "(F, A, C)"),
        (typing.Union[None, typing.Sequence[numbers.Number]], "F, A, C"),
        (typing.Union[None, typing.Sequence[numbers.Number]], "F#, A, Cb"),
        (
            typing.Union[
                numbers.Number, np.ndarray, typing.Sequence[numbers.Number]
            ],
            "MAJOR_TRIAD",
        ),
        (
            typing.Sequence[
                typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
            ],
            "[NATURAL_MINOR_SCALE]",
        ),
        (
            typing.Sequence[
                typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
            ],
            "NATURAL_MINOR_SCALE",
        ),
        (
            typing.Sequence[numbers.Number],
            "(OCTAVE,)",
        ),
        (
            typing.Sequence[numbers.Number],
            "OCTAVE",
        ),
        (
            typing.Sequence[
                typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
            ],
            "(MAJOR_TRIAD, MINOR_TRIAD)",
        ),
    ]
    to_fail = [
        (typing.Tuple[int, int], "(foo, 3)"),
        (typing.Union[numbers.Number, typing.Sequence[numbers.Number]], "foo"),
        (float, "SECOND"),
        (
            typing.Union[
                numbers.Number,
                typing.Sequence[numbers.Number],
            ],
            "foo",
        ),
    ]
    to_pass_with_val_dict = [
        (
            typing.Sequence[
                typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
            ],
            {"min_": (0,)},
            "[NATURAL_MINOR_SCALE]",
        ),
    ]
    empty_val_dict = {}

    for type_hint, value in to_pass:
        field = DummyField(value)
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
            raise AssertionError(f"{field}: {error}")


if __name__ == "__main__":
    test_type_validation()
