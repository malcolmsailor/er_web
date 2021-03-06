import re

from . import globals_


field_re = re.compile(r"`(\w+)`")
field_repl = '<code><a class="help-field-a" href="#{other_field}-div">{other_field}</a></code>'


def add_links():
    for field_name in globals_.ATTR_DICT:
        doc = globals_.ATTR_DICT[field_name]["doc"]
        other_fields = set(re.findall(field_re, doc))
        if not other_fields:
            continue
        for other_field in other_fields:
            if (
                other_field not in globals_.ATTR_DICT
                or other_field == field_name
            ):
                # TODO remove these extraneous fields?
                continue

            doc = doc.replace(
                # f"`{other_field}`", f"`[{other_field}](#{other_field}-div)`"
                f"`{other_field}`",
                field_repl.format(other_field=other_field),
            )
            # print(doc)
            # breakpoint()
        globals_.ATTR_DICT[field_name]["doc"] = doc
