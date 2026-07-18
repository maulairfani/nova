"""Chart Generation Tool (ADR-0026) — renders a chart from data the agent
already has (typically a prior *_sql_analytics result, still in its own
turn context) as a PNG via matplotlib, stored in MinIO's nova-charts
bucket. Not owned by any single business unit's data — the same
reasoning that placed the Web Search Tool on this server applies here."""
import io
import uuid
from typing import Literal

import matplotlib

matplotlib.use("Agg")  # headless container, no display/X server - must be
# set before pyplot's first import, which picks the backend at import time.
import matplotlib.pyplot as plt
from pydantic import BaseModel

from minio_client import ensure_bucket, get_client

_BUCKET = "nova-charts"

# Fixed categorical order, applied by series index and never reordered or
# cycled - validated for colorblind-safe adjacent contrast (this repo's
# dataviz skill / references/palette.md).
_SERIES_COLORS = [
    "#2a78d6",  # blue
    "#008300",  # green
    "#e87ba4",  # magenta
    "#eda100",  # yellow
    "#1baf7a",  # aqua
    "#eb6834",  # orange
    "#4a3aa7",  # violet
    "#e34948",  # red
]
_SURFACE = "#fcfcfb"
_INK_PRIMARY = "#0b0b0b"
_INK_SECONDARY = "#52514e"
_INK_MUTED = "#898781"
_GRIDLINE = "#e1e0d9"
_BASELINE = "#c3c2b7"


class ChartSeries(BaseModel):
    name: str
    values: list[float]


def _style_axes(ax) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=_GRIDLINE, linewidth=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(_BASELINE)
    ax.tick_params(colors=_INK_MUTED, labelsize=9)


async def generate_chart(
    title: str,
    chart_type: Literal["bar", "line", "pie"],
    labels: list[str],
    series: list[ChartSeries],
    x_label: str = "",
    y_label: str = "",
) -> dict:
    """Render `title` as a chart image so the employee can read data more
    easily than a table of numbers. Call this with data you already have
    from a prior business-unit analytics tool result in this same turn —
    `labels` are the category/x-axis values (e.g. months, DMAs, segments)
    and each `series` is one line/set of bars sharing those labels (e.g.
    one series per demographic segment or metric). Use "pie" only for a
    single series showing parts of a whole. Never try to describe the
    image itself in your reply — just mention a chart was generated; it
    is shown to the employee automatically, you don't need to link it."""
    if not series:
        return {"error": "At least one series is required."}
    if chart_type not in ("bar", "line", "pie"):
        # FastMCP/Pydantic already reject this via the Literal type at the
        # tool-calling boundary - this is defense-in-depth for direct
        # callers (tests, future refactors), same reasoning as db.py's
        # explicit NonSelectQueryError check rather than trusting the
        # system prompt alone.
        return {"error": f"Unsupported chart_type '{chart_type}'. Use 'bar', 'line', or 'pie'."}
    if chart_type == "pie" and len(series) != 1:
        return {"error": "A pie chart needs exactly one series."}
    for s in series:
        if len(s.values) != len(labels):
            return {"error": f"Series '{s.name}' has {len(s.values)} values but there are {len(labels)} labels."}

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    try:
        fig.patch.set_facecolor(_SURFACE)
        ax.set_facecolor(_SURFACE)

        if chart_type == "pie":
            colors = [_SERIES_COLORS[i % len(_SERIES_COLORS)] for i in range(len(labels))]
            ax.pie(
                series[0].values,
                labels=labels,
                colors=colors,
                autopct="%1.0f%%",
                textprops={"color": _INK_PRIMARY, "fontsize": 9},
            )
        else:
            _style_axes(ax)

            if chart_type == "bar":
                x = range(len(labels))
                n = len(series)
                width = min(0.8 / n, 0.32)
                for i, s in enumerate(series):
                    offset = (i - (n - 1) / 2) * width
                    ax.bar(
                        [xi + offset for xi in x],
                        s.values,
                        width=width,
                        label=s.name,
                        color=_SERIES_COLORS[i % len(_SERIES_COLORS)],
                    )
                ax.set_xticks(list(x))
                ax.set_xticklabels(labels)
            else:  # line
                for i, s in enumerate(series):
                    ax.plot(
                        labels,
                        s.values,
                        label=s.name,
                        color=_SERIES_COLORS[i % len(_SERIES_COLORS)],
                        linewidth=2,
                        marker="o",
                        markersize=5,
                    )

            if len(labels) > 6:
                plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
            if x_label:
                ax.set_xlabel(x_label, color=_INK_SECONDARY, fontsize=10)
            if y_label:
                ax.set_ylabel(y_label, color=_INK_SECONDARY, fontsize=10)
            # A single series needs no legend box - the title already
            # names it (dataviz skill's accessibility-pass rule).
            if len(series) > 1:
                ax.legend(frameon=False, labelcolor=_INK_SECONDARY, fontsize=9)

        ax.set_title(title, color=_INK_PRIMARY, fontsize=13, fontweight="bold", pad=14)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=_SURFACE)
        buf.seek(0)
    finally:
        plt.close(fig)

    chart_id = str(uuid.uuid4())
    client = get_client()
    ensure_bucket(client, _BUCKET)
    data = buf.getvalue()
    client.put_object(_BUCKET, f"{chart_id}.png", io.BytesIO(data), length=len(data), content_type="image/png")

    return {"chart_id": chart_id, "title": title, "chart_type": chart_type}
