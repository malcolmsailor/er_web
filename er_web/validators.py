import ast
import collections
import operator
import sys
import typing

import numpy as np

import wtforms

from . import safe_eval

CURRENT_MODULE = sys.modules[__name__]


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


min_.user_text = "Values must be >= {}"


def max_(x, max_x):
    comp_(x, max_x, operator.gt, "less than or equal to")


max_.user_text = "Values must be <= {}"


def open_min(x, min_x):
    comp_(x, min_x, operator.le, "greater than")


open_min.user_text = "Values must be > {}"


def open_max(x, max_x):
    comp_(x, max_x, operator.ge, "less than")


open_max.user_text = "Values must be < {}"


def get_type_specific_validator(type_, func_name, value_repl):
    g = getattr(CURRENT_MODULE, func_name)

    def f(x, *args, **kwargs):
        if not isinstance(x, type_):
            return
        return g(x, *args, **kwargs)

    f.user_text = g.user_text.replace("Values", value_repl)
    return f


for type_, str_ in ((int, "Integers"), (float, "Floats")):
    for func in (min_, max_, open_min, open_max):
        new_func_name = type_.__name__ + "_" + func.__name__
        if new_func_name[-1] == "_":
            new_func_name = new_func_name[:-1]
        new_func = get_type_specific_validator(type_, func.__name__, str_)
        setattr(CURRENT_MODULE, new_func_name, new_func)


def subseq_max_len(seq, max_len_):
    try:
        iter_ = iter(seq)
    except TypeError:
        # the argument is not a sequence. If this was not allowed, it would
        #   have failed type check previously, so we can return.
        return
    for subseq in iter_:
        try:
            len_ = len(subseq)
        except TypeError:
            continue
        if len_ > max_len_:
            msg = f"subsequences must have {max_len_} or fewer items"
            raise wtforms.validators.ValidationError(msg)


subseq_max_len.user_text = "Subsequences must have {} or fewer items"


def max_len(seq, max_len_):
    try:
        len_ = len(seq)
    except TypeError:
        # the argument is not a sequence. If this was not allowed, it would
        #   have failed type check previously, so we can return.
        return
    if len_ > max_len_:
        msg = f"sequence must have {max_len_} or fewer items"
        raise wtforms.validators.ValidationError(msg)


max_len.user_text = "Sequences must have {} or fewer items"


def equal_subseq_lens(seq):
    try:
        iter_ = iter(seq)
    except TypeError:
        # the argument is not a sequence. If this was not allowed, it would
        #   have failed type check previously, so we can return.
        return
    len_ = len(next(iter_))
    for subseq in iter_:
        if len_ != len(subseq):
            msg = "subsequences must all be of the same length"
            raise wtforms.validators.ValidationError(msg)


equal_subseq_lens.user_text = "Subsequences must all have the same length"


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
        # max_len(val)
        k_ty, v_ty = typing.get_args(type_hint)
        for k, v in val.items():
            _validate_type(k_ty, k)
            _validate_type(v_ty, v)
    elif isinstance(val, typing.Tuple):
        # max_len(val)
        sub_type_hint_tup = typing.get_args(type_hint)
        for sub_type_hint, sub_val in zip(sub_type_hint_tup, val):
            _validate_type(sub_type_hint, sub_val)
    elif isinstance(val, collections.abc.Sequence) and not isinstance(val, str):
        # max_len(val)
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


def validate_field(type_hint, val_dict, form, field):
    # We do not use the 'form' argument but it will be passed by flaskwtf

    try:
        if isinstance(field.data, bool):
            val = field.data
        elif not field.data:
            val = None
        else:
            # it should be a string
            data = str(field.data)
            # substitute any 'sharp signs' in the input
            data = data.replace("#", "_SHARP")
            if (
                "," in data
                or typing.get_origin(type_hint) == collections.abc.Sequence
            ) and data[0] not in "([{":
                data = "(" + data + (")" if data[-1] == "," else ",)")
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
