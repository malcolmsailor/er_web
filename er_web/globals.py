import efficient_rhythms
from .constants import ER_CONSTANTS

ATTR_DICT = {}
MAX_PRIORITY_DICT = {}
IGNORED_CATEGORIES = (
    "choir",
    "midi",
    "shell_only",
    "tuning",
)
CATEGORIES = tuple(
    c for c in efficient_rhythms.CATEGORIES if c not in IGNORED_CATEGORIES
)
