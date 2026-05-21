from __future__ import annotations


def _to_rgba(color: str | tuple[float, ...], alpha: float = 1.0) -> str:
    """Convert a color + alpha value to a plotly-compatible rgba string.

    Handles hex strings (``"#rrggbb"``) and float tuples (``(r, g, b)`` or
    ``(r, g, b, a)`` with components in [0, 1]).  Named CSS colors and other
    string formats are passed through unchanged; the *alpha* argument is
    ignored for them.
    """
    if isinstance(color, tuple):
        r = int(color[0] * 255)
        g = int(color[1] * 255)
        b = int(color[2] * 255)
        a = color[3] * alpha if len(color) == 4 else alpha
        return f"rgba({r},{g},{b},{a})"
    if isinstance(color, str) and color.startswith("#") and len(color) in (7, 9):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        if alpha == 1.0:
            return color
        return f"rgba({r},{g},{b},{alpha})"
    return color
