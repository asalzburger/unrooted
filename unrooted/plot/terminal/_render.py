"""Core rendering engine for the unicode terminal histogram backend."""
from __future__ import annotations

import numpy as np

MAX_BINS: int = 100

# Base markers, one per histogram index (0–3)
_SINGLE: tuple[str, ...] = (
    '○',  # ○  white circle          — index 0
    '✚',  # ✚  heavy greek cross     — index 1
    '□',  # □  white square          — index 2
    '·',  # ·  middle dot            — index 3
)

# Composite glyphs for cells where multiple histograms overlap.
# Keys are frozensets of histogram indices present in that cell.
_COMBO: dict[frozenset[int], str] = {
    frozenset({0}):          '○',  # ○
    frozenset({1}):          '✚',  # ✚
    frozenset({2}):          '□',  # □
    frozenset({3}):          '·',  # ·
    frozenset({0, 1}):       '⊕',  # ⊕  circled plus      (circle ∩ cross)
    frozenset({0, 2}):       '⊚',  # ⊚  circled ring      (circle ∩ square)
    frozenset({0, 3}):       '⊙',  # ⊙  circled dot       (circle ∩ dot)
    frozenset({1, 2}):       '⊞',  # ⊞  squared plus      (square ∩ cross)
    frozenset({1, 3}):       '✢',  # ✢  four-teardrop asterisk (cross ∩ dot)
    frozenset({2, 3}):       '⊡',  # ⊡  squared dot       (square ∩ dot)
    frozenset({0, 1, 2}):    '⊛',  # ⊛  circled asterisk
    frozenset({0, 1, 3}):    '⊕',  # ⊕  (best approx)
    frozenset({0, 2, 3}):    '⊙',  # ⊙  (best approx)
    frozenset({1, 2, 3}):    '⊞',  # ⊞  (best approx)
    frozenset({0, 1, 2, 3}): '✳',  # ✳  eight-spoked asterisk
}


def _fmt(v: float) -> str:
    """Format a numeric value for axis labels (compact, 3 significant figures)."""
    if v == 0.0:
        return '0'
    return f'{v:.3g}'


def _nice_interval(n: int) -> int:
    """Return the smallest 'nice' integer >= n from {1,2,5,10,20,25,50,100}."""
    for v in (1, 2, 5, 10, 20, 25, 50, 100):
        if v >= n:
            return v
    return 100


def render(
    values_list: list[np.ndarray],
    edges: np.ndarray,
    *,
    max_lines: int = 40,
    title: str = '',
    x_label: str = '',
    labels: list[str] | None = None,
    ratio: bool = False,
    ratio_lines: int = 10,
) -> str:
    """Render one or more 1D histogram value arrays as a unicode terminal string.

    Each bin occupies one character column; each plot row represents an equal
    fraction of the global y-maximum.  Overlapping histograms within the same
    cell are fused into a composite glyph from the ``_COMBO`` table.

    When *ratio* is ``True`` and at least two histograms are supplied, a ratio
    panel is appended below the main plot.  Each non-reference histogram is shown
    as a symbol at its ratio-to-reference row.  The ratio = 1 row is drawn as a
    dotted reference line (``·``); when a symbol lands exactly on that row it
    replaces the dot.

    Args:
        values_list: Bin values for each histogram (length-n arrays, same n).
        edges:       Bin edges, length n + 1.
        max_lines:   Height of the plot body in terminal rows (clamped to ≥ 5).
        title:       Optional title printed above the plot.
        x_label:     Optional x-axis label appended to the axis line.
        labels:      Optional legend labels, one per histogram.
        ratio:       When ``True``, append a ratio panel (requires ≥ 2 histograms).
        ratio_lines: Height of the ratio panel in rows (clamped to ≥ 4).

    Returns:
        A multi-line unicode string ready for ``print()``.

    Raises:
        ValueError: Too many bins, too many histograms, or empty input.
    """
    n_bins = len(edges) - 1
    n_hists = len(values_list)

    if n_hists == 0:
        raise ValueError('values_list must not be empty')
    if n_bins > MAX_BINS:
        raise ValueError(
            f'Terminal backend supports at most {MAX_BINS} bins, got {n_bins}'
        )
    if n_hists > 4:
        raise ValueError('Terminal backend supports at most 4 overlaid histograms')

    max_lines = max(max_lines, 5)
    show_ratio = ratio and n_hists > 1

    # ---------------------------------------------------------------- scaling
    global_max = max(
        (float(v.max()) for v in values_list if v.size > 0),
        default=0.0,
    )
    if global_max <= 0.0:
        global_max = 1.0  # avoid division by zero for empty/all-zero histograms

    scaled: list[np.ndarray] = [
        np.clip(np.round(vals / global_max * max_lines).astype(int), 0, max_lines)
        for vals in values_list
    ]

    # --------------------------------------------------------------- y-labels
    # Four ticks at 100 %, 75 %, 50 %, 25 % of max; "0" sits on the axis line.
    tick_rows = [0, max_lines // 4, max_lines // 2, 3 * max_lines // 4]
    tick_vals = {r: global_max * (max_lines - r) / max_lines for r in tick_rows}
    y_label_at: dict[int, str] = {r: _fmt(v) for r, v in tick_vals.items()}
    y_width_main = max(len(lb) for lb in list(y_label_at.values()) + ['0'])

    # ---------------------------------------------------- ratio y-width
    # Fixed range [0, 2] centred on 1.0; labels are "2", "1", "0".
    _R_MAX, _R_MIN = 2.0, 0.0
    ratio_lines = max(ratio_lines, 4)
    # Row where ratio = 1.0 lands (exact for even ratio_lines with [0,2] range)
    one_row = int(round((_R_MAX - 1.0) / (_R_MAX - _R_MIN) * ratio_lines))
    ratio_y_labels = [_fmt(_R_MAX), '1', _fmt(_R_MIN)]
    y_width_ratio = max(len(lb) for lb in ratio_y_labels) if show_ratio else 0
    y_width = max(y_width_main, y_width_ratio)

    # ------------------------------------------------------------- plot body
    body: list[str] = []
    for row in range(max_lines):
        chars: list[str] = []
        for col in range(n_bins):
            present = frozenset(
                i for i in range(n_hists)
                if int(scaled[i][col]) > max_lines - 1 - row
            )
            chars.append(_COMBO.get(present, ' '))
        y_str = y_label_at.get(row, '').rjust(y_width)
        body.append(f'{y_str} │{"".join(chars)}')  # │

    # axis line + optional x-labels (suppressed when ratio panel follows)
    axis = f'{"0".rjust(y_width)} └{"─" * n_bins}→'
    if x_label and not show_ratio:
        axis += f' {x_label}'
    body.append(axis)
    if not show_ratio:
        body.extend(_x_label_row(edges, y_width))

    # ----------------------------------------------------------------- title
    content_w = y_width + 2 + n_bins
    out: list[str] = []
    if title:
        out.append(title.center(content_w))
        out.append('')
    out.extend(body)

    # ---------------------------------------------------------------- legend
    if labels is not None:
        parts = [f'{_SINGLE[i]} {labels[i]}' for i in range(n_hists)]
        out.append('')
        out.append('  ' + '   '.join(parts))

    # -------------------------------------------------------------- ratio panel
    if show_ratio:
        ref = values_list[0]
        # For each non-reference histogram compute which row its ratio lands on.
        # Bins where ref == 0 get sentinel -1 (no data).
        ratio_row_arrays: list[np.ndarray] = []
        for vals in values_list[1:]:
            safe = ref > 0
            r_val = np.where(safe, vals / np.where(safe, ref, 1.0), np.nan)
            r_raw = (_R_MAX - r_val) / (_R_MAX - _R_MIN) * ratio_lines
            r_safe = np.where(np.isfinite(r_raw), r_raw, 0.0)
            r_int = np.where(
                np.isfinite(r_raw),
                np.clip(np.round(r_safe).astype(int), 0, ratio_lines - 1),
                -1,
            ).astype(int)
            ratio_row_arrays.append(r_int)

        # histogram indices in the ratio panel are 1, 2, … (to stay consistent
        # with _COMBO and _SINGLE which use the original overlay index)
        hist_idx = list(range(1, n_hists))

        ratio_y_label_at: dict[int, str] = {0: _fmt(_R_MAX), one_row: '1'}
        rbody: list[str] = []
        for row in range(ratio_lines):
            chars = []
            for col in range(n_bins):
                present = frozenset(
                    hist_idx[k]
                    for k, r in enumerate(ratio_row_arrays)
                    if r[col] == row
                )
                if present:
                    chars.append(_COMBO.get(present, '?'))
                elif row == one_row:
                    chars.append('·')
                else:
                    chars.append(' ')
            y_str = ratio_y_label_at.get(row, '').rjust(y_width)
            rbody.append(f'{y_str} │{"".join(chars)}')

        ratio_axis = f'{_fmt(_R_MIN).rjust(y_width)} └{"─" * n_bins}→'
        if x_label:
            ratio_axis += f' {x_label}'
        rbody.append(ratio_axis)
        rbody.extend(_x_label_row(edges, y_width))

        out.append('')
        out.extend(rbody)

    return '\n'.join(out)


def _x_label_row(edges: np.ndarray, y_width: int) -> list[str]:
    """Build the x-axis tick-label row and return it as a one-element list."""
    edge_strs = [_fmt(float(e)) for e in edges]
    max_lbl = max(len(s) for s in edge_strs)
    interval = _nice_interval(max_lbl + 1)
    offset = y_width + 2
    total = offset + len(edge_strs) - 1 + max_lbl + 4
    lrow = [' '] * total
    for i in range(0, len(edges), interval):
        lbl = edge_strs[i]
        start = offset + i - len(lbl) // 2
        for k, ch in enumerate(lbl):
            idx = start + k
            if 0 <= idx < total:
                lrow[idx] = ch
    return [''.join(lrow).rstrip()]
