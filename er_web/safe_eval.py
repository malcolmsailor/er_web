import ast
import operator
import os
import sys

from . import constants

# sys.path.insert(
#     0,
#     os.path.abspath(
#         os.path.join(
#             os.path.dirname(__file__),
#             "/Users/Malcolm/Google Drive/python/efficient_rhythms/src",
#         )
#     ),
# )

import efficient_rhythms.er_constants as er_constants

ALLOWED_OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Name):
        # rather than just directly looking for the id with
        # getattr(er_constants, id), I prefer to check it against a whitelist
        # first, since er_constants has other names defined like "np" or
        # "__builtins__"
        assert node.id in constants.ER_CONSTANTS
        return getattr(er_constants, node.id)
    elif isinstance(node, ast.BinOp):
        op = ALLOWED_OPERATIONS[
            node.op.__class__
        ]  # KeyError -> Unsafe operation
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Pow):
            assert right < 100
        return op(left, right)
    elif isinstance(node, ast.List):
        return [_safe_eval(elt) for elt in node.elts]
    elif isinstance(node, ast.Tuple):
        return tuple(_safe_eval(elt) for elt in node.elts)

    raise AssertionError("Unsafe operation")


def safe_eval(expr):
    """Simplified version of https://stackoverflow.com/a/30134081/10155119"""
    try:
        node = ast.parse(expr, "<string>", "eval").body
    except (TypeError, ValueError):
        raise ValueError
    return _safe_eval(node)
