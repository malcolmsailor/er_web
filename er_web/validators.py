import ast
import collections
import operator
import typing

import numpy as np

import wtforms

from . import globals_
from . import safe_eval


def comp_(x, y, op, op_str, seq=False):
    if isinstance(x, (collections.abc.Sequence, np.ndarray)) and not isinstance(
        x, str
    ):
        for z in x:
            comp_(z, y, op, op_str, seq=True)
    else:
        try:
            result = op(x, y)
        except TypeError:
            # this can occur, e.g., if the field can be None or have a numeric
            # value. We validate types elsewhere, so we shouldn't have to do
            # anything else here.
            return
        if result:
            msg = ("all values" if seq else "value") + f" must be {op_str} {y}"
            raise wtforms.validators.ValidationError(msg)


def min_(x, min_x):
    comp_(x, min_x, operator.lt, "greater than or equal to")


def max_(x, max_x):
    comp_(x, max_x, operator.gt, "less than or equal to")


def open_min(x, min_x):
    comp_(x, min_x, operator.le, "greater than")


def open_max(x, max_x):
    comp_(x, max_x, operator.ge, "greater than")


def max_len(seq, max_len_=globals_.MAX_SEQ_LEN):
    if len(seq) > max_len_:
        msg = f"sequence must have {max_len_} or fewer items"
        raise wtforms.validators.ValidationError(msg)


# er_const_splitter = re.compile(r"( ?[*/+-]+ ?)")
# ops = {
#     "*": operator.mul,
#     "/": operator.truediv,
#     "+": operator.add,
#     "-": operator.sub,
#     "//": operator.floordiv,
#     "**": operator.pow,
# }


# def _process_atom(atom):
#     # 1. check if atom is a defined constant
#     try:
#         return getattr(er_constants, atom)
#     except AttributeError:
#         pass
#     # 2. check if atom is a math operator
#     try:
#         return ops[atom.strip()]
#     except KeyError:
#         pass
#     # 3. check if atom is a number
#     try:
#         val = ast.literal_eval(atom)
#         assert isinstance(val, numbers.Number)
#         return val
#     except ValueError:
#         raise wtforms.validators.ValidationError
#     except TypeError:
#         raise wtforms.validators.ValidationError


# def process_er_constants(string):
#     # LONGTERM parse parentheses?
#     atoms = re.split(er_const_splitter, string)
#     atoms = [_process_atom(atom) for atom in atoms if atom]
#     val_stack = []
#     op_stack = []


def validate_field(type_hint, val_dict, form, field):
    # We do not use the 'form' argument but it will be passed by flaskwtf
    def _validate_type(type_hint, val):
        actual_type = typing.get_origin(type_hint) or type_hint
        if actual_type is typing.Union:
            for union_type in typing.get_args(type_hint):
                try:
                    _validate_type(union_type, val)
                    return
                except wtforms.validators.ValidationError as exc:
                    if "not of type" not in exc.__str__():
                        raise exc
            type_names = []
            for type_ in typing.get_args(type_hint):
                try:
                    # classes have __name__ attribute
                    type_names.append(type_.__name__)
                except AttributeError:
                    # type hints have _name attribute
                    type_names.append(type_._name)
            msg = f"Value {val} is not one of required types {type_names}"
            raise wtforms.validators.ValidationError(msg)
        if not isinstance(val, actual_type):
            if val is not None:
                try:
                    # this function actually *evaluates* the value, but we are
                    # not storing it anywhere, and then we evaluate it again
                    # later. surely that redundancy can be avoided! TODO
                    val = safe_eval.safe_eval(val)
                    _validate_type(type_hint, val)
                    return
                except (AssertionError, ValueError):
                    pass
            raise wtforms.validators.ValidationError(
                f"Value {val} is not of type {actual_type.__name__}"
            )
        if isinstance(val, typing.Dict):
            max_len(val)
            k_ty, v_ty = typing.get_args(type_hint)
            for k, v in val.items():
                _validate_type(k_ty, k)
                _validate_type(v_ty, v)
        elif isinstance(val, typing.Tuple):
            max_len(val)
            sub_type_hint_tup = typing.get_args(type_hint)
            for sub_type_hint, sub_val in zip(sub_type_hint_tup, val):
                _validate_type(sub_type_hint, sub_val)
        elif isinstance(val, collections.abc.Sequence) and not isinstance(
            val, str
        ):
            max_len(val)
            sub_type_hint_tup = typing.get_args(type_hint)
            # we expect this to only have one member
            # TODO handle gracefully
            assert len(sub_type_hint_tup) == 1
            sub_type_hint = sub_type_hint_tup[0]
            for sub_val in val:
                _validate_type(sub_type_hint, sub_val)
        if isinstance(val, str):
            if not actual_type == str:
                raise wtforms.validators.ValidationError(
                    f"Value {val} is not of type {actual_type.__name__}"
                )

    try:
        if isinstance(field.data, bool):
            val = field.data
        elif not field.data:
            val = None
        else:
            # it should be a string
            data = str(field.data)
            if "," in data and data[0] not in "([{":
                data = "(" + data + ")"
            try:
                val = ast.literal_eval(data)
            except ValueError:
                try:
                    # maybe it's an allowed math expression or a use of
                    # er_constants
                    val = safe_eval.safe_eval(data)
                except (AssertionError, ValueError):
                    # if none of these parse, let's try it as a string
                    val = data
        # else:
        #     val = field.data
        _validate_type(type_hint, val)
        for criterion, args in val_dict.items():
            # TODO I wonder if there is a better way of fetching the function?
            globals()[criterion](val, *args)
        field.validated_data = val
    except wtforms.validators.ValidationError as exc:
        raise
