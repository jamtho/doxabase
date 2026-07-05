"""Response and record types for doxabase.core (mechanical split).

Aggregator: star-imports the two part modules so every consumer keeps using
``from doxabase.core._types import *``. Definition order is preserved across
the parts; classes may depend on earlier ones (inheritance) and on _shared
constants.
"""
from __future__ import annotations

from doxabase.core._types_revisions import *  # noqa: F401,F403
from doxabase.core._types_descriptions import *  # noqa: F401,F403

from doxabase.core import _types_revisions as _revisions
from doxabase.core import _types_descriptions as _descriptions

__all__ = [*_revisions.__all__, *_descriptions.__all__]

del _revisions, _descriptions
