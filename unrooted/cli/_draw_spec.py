from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DrawType = Literal["hist", "prof", "th2", "eff", "branch"]
AutoStyleHint = Literal["hist", "profile", "efficiency"]

_TYPE_ALIASES: dict[str, DrawType] = {
    "hist": "hist",
    "th1": "hist",
    "h1": "hist",
    "th2": "th2",
    "h2": "th2",
    "prof": "prof",
    "profile": "prof",
    "tprofile": "prof",
    "eff": "eff",
    "efficiency": "eff",
    "branch": "branch",
    "tree": "branch",
}

_AUTO_STYLE: dict[DrawType, AutoStyleHint] = {
    "hist": "hist",
    "th2": "hist",
    "prof": "profile",
    "eff": "efficiency",
    "branch": "hist",
}


@dataclass
class DrawSpec:
    draw_type: DrawType
    keys: list[str]
    auto_style: AutoStyleHint


def parse_draw_spec(spec: str) -> DrawSpec:
    """Parse a draw specification string into a DrawSpec.

    Format: ``TYPE:KEY`` or multi-part depending on type:

    * ``hist:key/path``         — TH1 histogram (also ``th1:``, ``h1:``)
    * ``th2:key/path``          — TH2 histogram (also ``h2:``)
    * ``prof:key/path``         — TProfile histogram (also ``profile:``)
    * ``eff:pass_key:total_key``— efficiency from two TH1s
    * ``branch:tree:x_branch``  — TTree count histogram
    * ``branch:tree:x:y``       — TTree profile histogram

    For ``hist``, ``prof``, and ``th2`` types any colons inside the key path are
    treated as path separators and joined with ``/``, so both
    ``prof:somedata/eta`` and ``prof:somedata:eta`` resolve to the same
    ROOT path ``somedata/eta``.

    Args:
        spec: Raw draw specification string from the command line.

    Returns:
        Parsed :class:`DrawSpec`.

    Raises:
        ValueError: If the spec format is invalid.
    """
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(
            f"Invalid draw spec {spec!r}. Expected TYPE:KEY, e.g. 'hist:my_hist'."
        )

    raw_type = parts[0].lower()
    if raw_type not in _TYPE_ALIASES:
        known = ", ".join(sorted(set(_TYPE_ALIASES)))
        raise ValueError(
            f"Unknown draw type {raw_type!r} in spec {spec!r}. Valid types: {known}"
        )
    draw_type = _TYPE_ALIASES[raw_type]
    rest = parts[1:]

    if draw_type == "eff":
        if len(rest) != 2:
            raise ValueError(
                f"Efficiency spec requires exactly 2 keys: 'eff:pass_key:total_key'. "
                f"Got: {spec!r}"
            )
        keys = rest
    elif draw_type == "branch":
        if not 2 <= len(rest) <= 3:
            raise ValueError(
                f"Branch spec requires 2 or 3 keys: 'branch:tree:x[:y]'. Got: {spec!r}"
            )
        keys = rest
    else:
        # hist, prof, th2: colons inside path are path separators → join with /
        keys = ["/".join(rest)]

    return DrawSpec(draw_type=draw_type, keys=keys, auto_style=_AUTO_STYLE[draw_type])
