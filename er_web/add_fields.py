import functools
import json
import re
import typing

import wtforms

from . import globals
from . import validators


def _add_boolean_field(form_cls, field_name, default_val):
    wtfield = wtforms.BooleanField(field_name, default=default_val)
    setattr(form_cls, field_name, wtfield)
    globals.DEFAULT_FIELD_VALUES[field_name] = "y" if default_val else "n"


def _add_select_field(form_cls, field_name, choices, default_val):
    wtfield = wtforms.SelectField(
        field_name, default=default_val, choices=choices
    )
    setattr(form_cls, field_name, wtfield)
    globals.DEFAULT_FIELD_VALUES[field_name] = str(default_val)


poss_const_re = re.compile(r"'\w+'")


def get_default(field_name, field_val):
    if field_name in globals.WEB_DEFAULTS:
        return globals.WEB_DEFAULTS[field_name]
    if field_val is None:
        return ""
    if isinstance(field_val, bool):
        return field_val
    # why isn't this working for hard_bounds?
    field_val = str(field_val)
    poss_consts = [(s, s[1:-1]) for s in re.findall(poss_const_re, field_val)]
    for quoted, unquoted in poss_consts:
        if unquoted in globals.ER_CONSTANTS:
            field_val = field_val.replace(quoted, unquoted)
    return field_val


def add_fields_to_form(cls_or_obj, form_cls):
    for field_name, field_args in cls_or_obj.__dataclass_fields__.items():

        metadata = field_args.metadata
        category = metadata["category"]
        priority = metadata["priority"]
        field_type = field_args.type
        if "shell_only" in metadata and metadata["shell_only"]:
            continue
        if category in globals.IGNORED_CATEGORIES:
            continue
        if priority == 0:
            continue
        globals.ATTR_DICT[field_name] = field_dict = {}
        if field_name in globals.DOCS:
            field_dict["doc"] = globals.DOCS[field_name]
        else:
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

        default = get_default(field_name, field_val)

        if field_type is bool:
            _add_boolean_field(form_cls, field_name, default)
            continue
        elif "possible_values" in metadata:
            _add_select_field(
                form_cls, field_name, metadata["possible_values"], default
            )
            continue
        if field_name in globals.VAL_DICTS:
            val_dict = globals.VAL_DICTS[field_name]
        else:
            try:
                val_dict = metadata["val_dict"]
            except KeyError:
                val_dict = {}
        validator = functools.partial(
            validators.validate_field, field_type, val_dict
        )

        wtfield = wtforms.StringField(
            field_name, default=default, validators=[validator]
        )
        globals.DEFAULT_FIELD_VALUES[field_name] = str(default)

        setattr(form_cls, field_name, wtfield)
