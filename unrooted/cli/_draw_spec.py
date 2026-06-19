from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DrawType = Literal["hist", "prof", "th2", "eff", "branch"]
AutoStyleHint = Literal["hist", "profile", "efficiency", "scatter"]
BranchSubType = Literal["count", "prof", "scatter"]

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
    "branch": "hist",  # overridden per branch_sub_type during parsing
}

_BRANCH_SUBTYPES = {"prof", "scatter"}


@dataclass
class DrawSpec:
    draw_type: DrawType
    keys: list[str]
    auto_style: AutoStyleHint
    branch_sub_type: BranchSubType | None = None


def parse_draw_spec(spec: str) -> DrawSpec:
    """Parse a draw specification string into a DrawSpec.

    Format: ``TYPE:KEY`` or multi-part depending on type:

    * ``hist:key/path``                — TH1 histogram (also ``th1:``, ``h1:``)
    * ``th2:key/path``                 — TH2 histogram (also ``h2:``)
    * ``prof:key/path``                — TProfile histogram (also ``profile:``)
    * ``eff:pass_key:total_key``       — efficiency from two TH1s
    * ``branch:tree:x_branch``         — TTree count histogram
    * ``branch:tree:prof:x:y``         — TTree profile histogram
    * ``branch:tree:scatter:x:y``      — TTree scatter plot

    For ``hist``, ``prof``, and ``th2`` types any colons inside the key path
    are treated as path separators and joined with ``/``, so both
    ``prof:somedata/eta`` and ``prof:somedata:eta`` resolve to the same ROOT
    path ``somedata/eta``.

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
        return DrawSpec(
            draw_type=draw_type,
            keys=rest,
            auto_style=_AUTO_STYLE[draw_type],
        )

    if draw_type == "branch":
        return _parse_branch_spec(spec, rest)

    # hist, prof, th2: colons inside path are path separators → join with /
    return DrawSpec(
        draw_type=draw_type,
        keys=["/".join(rest)],
        auto_style=_AUTO_STYLE[draw_type],
    )


def _parse_branch_spec(spec: str, rest: list[str]) -> DrawSpec:
    """Parse the `rest` parts of a ``branch:`` draw spec.

    Accepted formats (rest = everything after the leading ``branch`` token):

    * ``[tree, x]``                     → count histogram
    * ``[tree, "prof", x, y]``          → profile histogram
    * ``[tree, "scatter", x, y]``       → scatter plot

    The old implicit profile format ``[tree, x, y]`` (three parts) is no
    longer accepted.  Use ``branch:tree:prof:x:y`` instead.
    """
    if len(rest) < 2:
        raise ValueError(
            f"Branch spec requires at least tree and x-branch: "
            f"'branch:tree:x_branch'. Got: {spec!r}"
        )

    tree_key = rest[0]

    # Detect subtype from the second token.
    if rest[1] in _BRANCH_SUBTYPES:
        sub_type_str = rest[1]
        branch_args = rest[2:]
        if len(branch_args) != 2:
            raise ValueError(
                f"Branch spec 'branch:tree:{sub_type_str}:x:y' requires exactly "
                f"2 branch names after the subtype. Got: {spec!r}"
            )
        x_branch, y_branch = branch_args
        sub_type: BranchSubType = sub_type_str  # type: ignore[assignment]
        auto_style: AutoStyleHint = "scatter" if sub_type == "scatter" else "profile"
        return DrawSpec(
            draw_type="branch",
            keys=[tree_key, x_branch, y_branch],
            auto_style=auto_style,
            branch_sub_type=sub_type,
        )

    # Count histogram: branch:tree:x_branch
    if len(rest) == 2:
        return DrawSpec(
            draw_type="branch",
            keys=[tree_key, rest[1]],
            auto_style="hist",
            branch_sub_type="count",
        )

    # Old implicit profile format — guide the user to the new syntax.
    if len(rest) == 3:
        raise ValueError(
            f"Implicit profile format 'branch:tree:x:y' is no longer supported. "
            f"Use 'branch:{rest[0]}:prof:{rest[1]}:{rest[2]}' instead. "
            f"Got: {spec!r}"
        )

    raise ValueError(
        f"Unrecognised branch spec format. Expected 'branch:tree:x', "
        f"'branch:tree:prof:x:y', or 'branch:tree:scatter:x:y'. Got: {spec!r}"
    )
