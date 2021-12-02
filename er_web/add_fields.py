import collections
import functools
import re
import typing


import markdown
import wtforms
import wtforms.fields.html5

import efficient_rhythms

from . import globals_
from . import validators
from . import constants


def add_density(field_dict, field_type, metadata):
    has_density = efficient_rhythms.er_types.has_density(field_type)
    field_dict["has_density"] = has_density
    if has_density:
        field_dict["more_density"] = metadata["more"]
        field_dict["less_density"] = metadata["less"]


def _add_boolean_field(form_cls, field_name, default_val):
    wtfield = wtforms.BooleanField(field_name, default=default_val)
    setattr(form_cls, field_name, wtfield)
    globals_.DEFAULT_FIELD_VALUES[field_name] = "y" if default_val else "n"


def _add_select_field(form_cls, field_name, choices, default_val):
    wtfield = wtforms.SelectField(
        field_name, default=default_val, choices=choices
    )
    setattr(form_cls, field_name, wtfield)
    globals_.DEFAULT_FIELD_VALUES[field_name] = str(default_val)


poss_const_re = re.compile(r"'\w+'")


def get_default(field_name, field_val):
    if field_name in globals_.WEB_DEFAULTS:
        return globals_.WEB_DEFAULTS[field_name]
    if field_val is None:
        return ""
    if isinstance(field_val, bool):
        return field_val
    # why isn't this working for hard_bounds?
    field_val = str(field_val)
    poss_consts = [(s, s[1:-1]) for s in re.findall(poss_const_re, field_val)]
    for quoted, unquoted in poss_consts:
        if unquoted in constants.ER_CONSTANTS:
            field_val = field_val.replace(quoted, unquoted)
    if (field_val[0] == "(" and field_val[-1] == ")") or (
        field_val[0] == "[" and field_val[-1] == "]"
    ):
        return field_val[1:-1]
    return field_val


def get_typing_string(field_args, val_dict):
    def _concat_strings(strings, abbrev_i):
        if not strings:
            return ""
        if len(strings) == 1:
            return strings[0] + "."
        if len(strings) == 2:

            return strings[0] + " and " + strings[1][abbrev_i:] + "."
        return (
            strings[0]
            + ", "
            + ",".join([s[abbrev_i:] for s in strings[1:-1]])
            + ", and "
            + strings[-1][abbrev_i:]
            + "."
        )

    try:
        typing_string = globals_.TYPING_STRINGS[field_args.type]
    except KeyError:
        # TODO
        typing_string = ""
    val_strings = []
    for func_name, args in val_dict.items():
        func = getattr(validators, func_name)
        user_text = getattr(func, "user_text")
        val_strings.append(user_text.format(*args))
    if not val_strings:
        return markdown.markdown(typing_string)

    v_strings = [s for s in val_strings if s.startswith("Values")]
    i_strings = [s for s in val_strings if s.startswith("Integers")]
    f_strings = [s for s in val_strings if s.startswith("Floats")]
    s_strings = [s for s in val_strings if s.startswith("Sequences")]
    u_strings = [s for s in val_strings if s.startswith("Subsequences")]
    # Replace 'Value must be ' at beginning of subsequent strings
    v_string = _concat_strings(v_strings, 15)
    i_string = _concat_strings(i_strings, 17)
    f_string = _concat_strings(f_strings, 15)
    v_string = " ".join([v_string, i_string, f_string])
    s_string = _concat_strings(s_strings, 10)
    u_string = _concat_strings(u_strings, 13)
    out = [typing_string + ".", v_string, s_string, u_string]
    return markdown.markdown("\n\n".join(out))


def _is_seq(type_hint):
    def _sub(type_hint):
        origin = typing.get_origin(type_hint)
        if origin == collections.abc.Sequence:
            return True, typing.get_args(type_hint)
        elif origin == typing.Union:
            union_types = typing.get_args(type_hint)
            for t in union_types:
                if typing.get_origin(t) == collections.abc.Sequence:
                    return True, typing.get_args(t)
        return False, None

    seq, sub_type_hints = _sub(type_hint)
    if not seq:
        return False, False
    for sub_type_hint in sub_type_hints:
        subseq, _ = _sub(sub_type_hint)
        if subseq:
            return seq, subseq
    return seq, False


def get_val_dict(metadata, field_name, field_type):
    try:
        val_dict = metadata["val_dict"]
    except KeyError:
        val_dict = {}
    if field_name in globals_.VAL_DICTS:
        val_dict.update(globals_.VAL_DICTS[field_name])
    seq, subseq = _is_seq(field_type)
    if seq and "max_len" not in val_dict:
        val_dict["max_len"] = (globals_.MAX_SEQ_LEN,)
    if subseq and "subseq_max_len" not in val_dict:
        val_dict["subseq_max_len"] = (globals_.MAX_SUBSEQ_LEN,)
    return val_dict


def get_constants(field_dict, metadata):
    def _get_label(group):
        try:
            return globals_.CONSTANT_GROUP_LABELS[group]
        except KeyError:
            return group  # TODO make sure all labels are in this dict

    out = {}
    if "expected_constants" in metadata:
        constant_groups = metadata["expected_constants"]
        for group in constant_groups:

            if group in globals_.CONSTANT_GROUPS:
                out[_get_label(group)] = globals_.CONSTANT_GROUPS[group]
            elif group in globals_.CONSTANT_SUPER_GROUPS:
                for subgroup in globals_.CONSTANT_SUPER_GROUPS[group]:
                    out[_get_label(subgroup)] = globals_.CONSTANT_GROUPS[
                        subgroup
                    ]
            else:
                out[_get_label(group)] = efficient_rhythms.CONSTANT_GROUPS[
                    group
                ]
        # field_dict["expected_constants"] = tuple(
        #     item for list_ in expected_constants for item in list_
        # )
    field_dict["expected_constants"] = out


def get_doc(field_name, metadata):
    if field_name in globals_.DOCS:
        return markdown.markdown(globals_.DOCS[field_name])
    else:
        return markdown.markdown(metadata["mutable_attrs"]["doc"])


def get_pretty_name(field_name, abbrevs=globals_.FIELD_NAME_ABBREVS):
    bits = field_name.split("_")
    return " ".join(
        abbrevs[bit] if bit in abbrevs else bit for bit in bits
    ).capitalize()


def add_fields_to_form(cls_or_obj, form_cls):
    for field_name, field_args in cls_or_obj.__dataclass_fields__.items():
        if field_name[0] == "_":
            # ignore private fields
            continue

        metadata = field_args.metadata
        category = metadata["category"]
        priority = metadata["priority"]
        field_type = field_args.type
        if "shell_only" in metadata and metadata["shell_only"]:
            continue
        if category in globals_.IGNORED_CATEGORIES:
            continue
        if priority == 0:
            continue
        globals_.ATTR_DICT[field_name] = field_dict = {}

        field_dict["doc"] = get_doc(field_name, metadata)
        field_dict["priority"] = priority
        field_dict["category"] = category
        field_dict["pretty_name"] = get_pretty_name(field_name)

        if category not in globals_.MAX_PRIORITY_DICT:
            globals_.MAX_PRIORITY_DICT[category] = priority
        elif globals_.MAX_PRIORITY_DICT[category] < priority:
            globals_.MAX_PRIORITY_DICT[category] = priority
        try:
            field_val = getattr(cls_or_obj, field_name)
        except AttributeError:
            # this happens when passed a class that has a default_factory
            field_val = field_args.default_factory()

        default = get_default(field_name, field_val)
        get_constants(field_dict, metadata)

        if field_type is bool:
            _add_boolean_field(form_cls, field_name, default)
            continue
        # elif efficient_rhythms.er_types.has_density(field_type):
        #     _add_density_field(form_cls, field_type, field_name, default)
        #     continue
        elif "possible_values" in metadata:
            _add_select_field(
                form_cls, field_name, metadata["possible_values"], default
            )
            continue
        add_density(field_dict, field_type, metadata)

        val_dict = get_val_dict(metadata, field_name, field_type)
        field_dict["typing_string"] = get_typing_string(field_args, val_dict)
        validator = functools.partial(
            validators.validate_field, field_type, val_dict
        )

        wtfield = wtforms.StringField(
            field_name, default=default, validators=[validator]
        )
        globals_.DEFAULT_FIELD_VALUES[field_name] = str(default)

        setattr(form_cls, field_name, wtfield)
