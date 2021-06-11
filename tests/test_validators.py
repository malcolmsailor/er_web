import numbers
import os
import sys
import traceback
import typing

import numpy as np

import wtforms

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_web.validators as validators
import er_web.forms as forms

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


class DummyField:
    def __init__(self, data):
        self.data = data


def test_validators():
    to_pass = [
        (str, "foo"),
        (typing.Tuple[int, int], "(2, 3)"),
        (int, "SECOND"),
        (bool, "True"),
        (typing.Union[bool, typing.Sequence[bool]], "True, False, True"),
        (typing.Union[None, typing.Tuple[int]], ""),
        (typing.Union[None, typing.Tuple[int]], "(2,)"),
        (typing.Union[None, typing.Tuple[int]], "2,"),
        (typing.Union[None, typing.Tuple[int]], "None"),
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
            typing.Sequence[numbers.Number],
            "(OCTAVE,)",
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
    try:
        for type_hint, value in to_pass:
            field = DummyField(value)
            validators.validate_field(type_hint, empty_val_dict, None, field)
        for type_hint, val_dict, value in to_pass_with_val_dict:
            field = DummyField(value)
            validators.validate_field(type_hint, val_dict, None, field)
        for type_hint, value in to_fail:
            field = DummyField(value)
            try:
                validators.validate_field(
                    type_hint, empty_val_dict, None, field
                )
            except wtforms.validators.ValidationError:
                continue
            else:
                raise AssertionError(
                    "There should have been a validation error"
                )
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


def test_form_validation():
    # default form
    import flask

    app = flask.Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",  # TODO
    )
    with app.app_context():
        form = forms.ERForm({})
        try:
            assert form.validate()
        except:  # pylint: disable=bare-except

            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()


if __name__ == "__main__":
    test_validators()
    test_form_validation()
