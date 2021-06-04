import functools
import re
import typing

import wtforms

from . import globals
from . import validators


def _add_boolean_field(form_cls, field_name, default_val):
    wtfield = wtforms.BooleanField(field_name, default=default_val)
    setattr(form_cls, field_name, wtfield)


def _add_select_field(form_cls, field_name, choices, default_val):
    wtfield = wtforms.SelectField(
        field_name, default=default_val, choices=choices
    )
    setattr(form_cls, field_name, wtfield)


poss_const_re = re.compile(r"'\w+'")


def get_default(field_val):
    if field_val is None:
        return ""
    # why isn't this working for hard_bounds?
    field_val = str(field_val)
    poss_consts = [(s, s[1:-1]) for s in re.findall(poss_const_re, field_val)]
    for quoted, unquoted in poss_consts:
        if unquoted in globals.ER_CONSTANTS:
            field_val = field_val.replace(quoted, unquoted)
    return field_val


def add_fields_to_form(cls_or_obj, form_cls):
    for field_name, field_args in cls_or_obj.__dataclass_fields__.items():
        globals.ATTR_DICT[field_name] = field_dict = {}
        metadata = field_args.metadata
        category = metadata["category"]
        priority = metadata["priority"]
        field_type = field_args.type
        if "shell_only" in metadata and metadata["shell_only"]:
            continue
        if category in globals.IGNORED_CATEGORIES:
            continue
        field_dict["doc"] = metadata["mutable_attrs"]["doc"]
        field_dict["priority"] = priority
        field_dict["category"] = category
        if category not in globals.MAX_PRIORITY_DICT:
            globals.MAX_PRIORITY_DICT[category] = priority
        elif globals.MAX_PRIORITY_DICT[category] < priority:
            globals.MAX_PRIORITY_DICT[category] = priority
        try:
            field_val = getattr(cls_or_obj, field_name)
        except AttributeError:
            # this happens when passed a class that has a default_factory
            field_val = field_args.default_factory()
        if field_type is bool:
            _add_boolean_field(form_cls, field_name, field_val)
            continue
        elif "possible_values" in metadata:
            _add_select_field(
                form_cls, field_name, metadata["possible_values"], field_val
            )
            continue
        try:
            val_dict = metadata["val_dict"]
        except KeyError:
            val_dict = {}
        validator = functools.partial(
            validators.validate_field, field_type, val_dict
        )
        default = get_default(field_val)
        wtfield = wtforms.StringField(
            field_name, default=default, validators=[validator]
        )

        setattr(form_cls, field_name, wtfield)
