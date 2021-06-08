import ast
import collections
import operator
import typing

import wtforms

# from wtforms.validators import ValidationError

from . import safe_eval


def comp_(x, y, op, op_str, seq=False):
    if isinstance(x, collections.abc.Sequence) and not isinstance(x, str):
        for z in x:
            comp_(z, y, op, op_str, seq=True)
    elif op(x, y):
        msg = ("all values" if seq else "value") + f" must be {op_str} {y}"
        raise wtforms.validators.ValidationError(msg)


def min_(x, min_x):
    comp_(x, min_x, operator.lt, "greater than or equal to")


def max_(x, max_x):
    comp_(x, max_x, operator.gt, "less than or equal to")


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
    def _validate_type(type_hint, val):
        actual_type = typing.get_origin(type_hint) or type_hint
        if actual_type is typing.Union:
            for union_type in typing.get_args(type_hint):
                print("union type: ", union_type)
                try:
                    _validate_type(union_type, val)
                except wtforms.validators.ValidationError:
                    continue
                return
            # TODO error messages
            raise wtforms.validators.ValidationError(
                f"Value {val} is not of type {actual_type}"
            )
        if not isinstance(val, actual_type):
            if val is not None:
                try:
                    # this function actually *evaluates* the value, but we are not
                    # storing it anywhere, and then we evaluate it again later.
                    # surely that redundancy can be avoided! TODO
                    val = safe_eval.safe_eval(val)
                    _validate_type(type_hint, val)
                    return
                except (AssertionError, ValueError):
                    pass
            raise wtforms.validators.ValidationError(
                f"Value {val} is not of type {actual_type}"
            )
        if isinstance(val, typing.Dict):
            k_ty, v_ty = typing.get_args(type_hint)
            for k, v in val.items():
                _validate_type(k_ty, k)
                _validate_type(v_ty, v)
        elif isinstance(val, typing.Tuple):
            sub_type_hint_tup = typing.get_args(type_hint)
            for sub_type_hint, sub_val in zip(sub_type_hint_tup, val):
                _validate_type(sub_type_hint, sub_val)
        elif isinstance(val, collections.abc.Sequence) and not isinstance(
            val, str
        ):
            sub_type_hint_tup = typing.get_args(type_hint)
            # we expect this to only have one member
            # TODO handle gracefully
            assert len(sub_type_hint_tup) == 1
            sub_type_hint = sub_type_hint_tup[0]
            for sub_val in val:
                _validate_type(sub_type_hint, sub_val)

    try:
        # print(field.data, type(field.data))
        if not field.data:
            val = None
        else:
            try:
                val = ast.literal_eval(field.data)
            except ValueError:
                try:
                    # maybe it's an allowed math expression
                    val = safe_eval.safe_eval(field.data)
                except (AssertionError, ValueError):
                    try:
                        # maybe it's a sequence with the external brackets/
                        # parentheses missing
                        val = ast.literal_eval("(" + field.data + ")")
                    except ValueError:
                        # if none of these parse, let's try it as a string
                        val = field.data
        # print(val, type(val))
        # print(type_hint)
        _validate_type(type_hint, val)
        for criterion, args in val_dict.items():
            # TODO I wonder if there is a better way of fetching the function?
            globals()[criterion](val, *args)
        field.validated_data = val
    except wtforms.validators.ValidationError:
        raise
    except:  # pylint: disable=bare-except
        # TODO delete this except clause
        import sys
        import traceback

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()
