"""Module with function that creates pdf from a given plt.figure."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch
from PIL import Image

from src.helpers.time.time import get_sidereal_time

if TYPE_CHECKING:
    from src.stereographic_projection.stereographic_projector import (
        StereoProjConfig,
    )


# ─── Visual constants ────────────────────────────────────────────────────────

COLOR_PRIMARY = "#0D1B2A"  # deep navy
COLOR_ACCENT = "#4A90D9"  # stellar blue
COLOR_ACCENT2 = "#F0A500"  # golden highlight
COLOR_BG = "#FFFFFF"
COLOR_MUTED = "#6B7A8D"
COLOR_RULE = "#C9D6E3"

LOGO_ZOOM_DEFAULT = 0.15  # base zoom (≈1.5× the old 0.1)
LOGO_POSITION = (0.06, 0.93)  # slightly right & down compared to (0.02, 0.95)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def add_logo_to_figure(
    fig: plt.Figure,
    logo_path: str | None = None,
    position: tuple[float, float] = LOGO_POSITION,
    size: float = LOGO_ZOOM_DEFAULT,
):
    """Add a logo to the figure (1.5× larger than before, repositioned)."""
    try:
        logo = Image.open(logo_path)
        logo_array = np.array(logo)
        im = OffsetImage(logo_array, zoom=size)
        ab = AnnotationBbox(
            im,
            position,
            xycoords="figure fraction",
            frameon=False,
            box_alignment=(0, 1),
        )
        fig.add_artist(ab)
    except Exception as e:
        print(f"Error loading logo: {e}")


def add_footer_text(
    fig: plt.Figure,
    text: str,
    position: tuple[float, float] = (0.5, 0.02),
    fontsize: int = 8,
    color: str = COLOR_MUTED,
):
    """Add footer text to the figure."""
    fig.text(
        position[0],
        position[1],
        text,
        fontsize=fontsize,
        color=color,
        ha="center",
        va="bottom",
        transform=fig.transFigure,
        fontfamily="monospace",
    )


def _draw_page_template(
    fig: plt.Figure,
    title: str,
    subtitle: str = "",
    page_size: tuple[float, float] = (8.27, 11.69),
):
    """
    Draw a styled page template with header band and decorative rules.

    The header occupies the top ~12% of the figure (in figure-fraction coords).
    """
    w, h = page_size

    # ── Header background band ──────────────────────────────────────────────
    header_ax = fig.add_axes([0, 0.885, 1, 0.115], zorder=0)
    header_ax.set_xlim(0, 1)
    header_ax.set_ylim(0, 1)
    header_ax.axis("off")

    # Dark navy background
    header_ax.add_patch(
        mpatches.Rectangle(
            (0, 0),
            1,
            1,
            facecolor=COLOR_PRIMARY,
            edgecolor="none",
            transform=header_ax.transAxes,
            zorder=1,
        )
    )

    # Golden accent stripe at the very top
    header_ax.add_patch(
        mpatches.Rectangle(
            (0, 0.88),
            1,
            0.12,
            facecolor=COLOR_ACCENT2,
            edgecolor="none",
            transform=header_ax.transAxes,
            zorder=2,
        )
    )

    # Title text
    header_ax.text(
        0.5,
        0.52,
        title,
        transform=header_ax.transAxes,
        fontsize=16,
        fontweight="bold",
        color="white",
        ha="center",
        va="center",
        zorder=3,
        fontfamily="monospace",
    )

    # Subtitle text
    if subtitle:
        header_ax.text(
            0.5,
            0.18,
            subtitle,
            transform=header_ax.transAxes,
            fontsize=9,
            color=COLOR_ACCENT,
            ha="center",
            va="center",
            zorder=3,
            fontfamily="monospace",
            style="italic",
        )

    # ── Horizontal rule below header ────────────────────────────────────────
    rule_ax = fig.add_axes([0.05, 0.875, 0.90, 0.002], zorder=0)
    rule_ax.set_facecolor(COLOR_ACCENT)
    rule_ax.axis("off")

    # ── Thin decorative bottom rule ─────────────────────────────────────────
    bottom_rule_ax = fig.add_axes([0.05, 0.055, 0.90, 0.001], zorder=0)
    bottom_rule_ax.set_facecolor(COLOR_RULE)
    bottom_rule_ax.axis("off")


def _draw_task_block(
    fig: plt.Figure,
    tasks: list[dict],  # each: {'label': str, 'description': str}
    y_start: float = 0.855,
    x_left: float = 0.07,
    x_right: float = 0.93,
    label_fontsize: int = 11,
    desc_fontsize: int = 9,
    block_gap: float = 0.068,
):
    """
    Draw numbered task blocks with label + helper description.
    Each block has a coloured index badge, bold label and italic description.
    """
    y = y_start
    for i, task in enumerate(tasks, 1):
        # ── Badge circle ────────────────────────────────────────────────────
        badge_ax = fig.add_axes(
            [x_left - 0.015, y - 0.022, 0.032, 0.032],
            zorder=5,
        )
        badge_ax.set_xlim(0, 1)
        badge_ax.set_ylim(0, 1)
        badge_ax.axis("off")
        badge_ax.add_patch(
            plt.Circle(
                (0.5, 0.5),
                0.48,
                facecolor=COLOR_ACCENT,
                edgecolor="none",
                transform=badge_ax.transAxes,
            )
        )
        badge_ax.text(
            0.5,
            0.5,
            str(i),
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
            fontfamily="monospace",
        )

        # ── Checkbox + task label ───────────────────────────────────────────
        fig.text(
            x_left + 0.025,
            y,
            task["label"],
            fontsize=label_fontsize,
            va="top",
            color=COLOR_PRIMARY,
            fontfamily="monospace",
            fontweight="bold",
        )

        # ── Helper description ──────────────────────────────────────────────
        if task.get("description"):
            fig.text(
                x_left + 0.055,
                y - 0.028,
                task["description"],
                fontsize=desc_fontsize,
                va="top",
                color=COLOR_MUTED,
                fontfamily="monospace",
                style="italic",
                wrap=True,
            )

        y -= block_gap


# ─── Public save functions ───────────────────────────────────────────────────


def save_figure(
    fig: plt.Figure,
    filename: str,
    logo_path: str | None = None,
    footer_text: str | None = None,
    dpi: int = 300,
    logo_position: tuple[float, float] = LOGO_POSITION,
    text_position: tuple[float, float] = (0.5, 0.02),
):
    """Save figure as PDF with logo and footer text."""
    if logo_path:
        add_logo_to_figure(fig, logo_path, logo_position)
    if footer_text:
        add_footer_text(fig, footer_text, text_position)
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    fig.savefig(filename, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    logger.info(f"Figure saved as '{filename}'")


def save_figure_pinhole(
    fig: plt.Figure,
    filename: str,
    logo_path: str | None = None,
    footer_text: str | None = None,
    dpi: int = 300,
    logo_position: tuple[float, float] = LOGO_POSITION,
    text_position: tuple[float, float] = (0.5, 0.02),
    page_size: tuple[float, float] = (11.69, 8.27),
    chart_margins: tuple[float, float, float, float] = (0.1, 0.2, 0.1, 0.1),
):
    """
    Save figure as PDF with logo and footer text
    (for pinhole / camera obscura result).
    """
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    resolved_logo_path = _resolve_logo(logo_path)

    # ── Tasks definition for pinhole / camera obscura ─────────────────────
    tasks = [
        {
            "label": "Обозначьте созвездия",
            "description": (
                "Найдите на снимке видимые созвездия и подпишите каждое\n"
                "трёхбуквенным латинским сокращением (Ori, UMa, Cas…).\n"
                "Соедините главные звёзды, проведя контуры созвездий."
            ),
        },
        {
            "label": "Проведите эклиптику",
            "description": (
                "Эклиптика —"
                "видимый путь Солнца среди звёзд (наклонена к экватору\n"
                "на ε ≈ 23°26′)."
                "Нанесите её, если она попадает в поле зрения снимка."
            ),
        },
        {
            "label": "Проведите небесный экватор",
            "description": (
                "Небесный экватор —"
                "проекция земного экватора на небесную сферу.\n"
                "Нанесите его дугой, если он присутствует на снимке."
            ),
        },
        {
            "label": "Обозначьте точку равноденствия",
            "description": (
                "Нанесите точки осеннего или весеннего равноденствия,"
                "если они видны.\n"
                "Это точки пересечения эклиптики с небесным экватором."
            ),
        },
    ]

    with PdfPages(filename) as pdf:
        plt.rcParams["font.family"] = "monospace"

        # ── Info / task page ───────────────────────────────────────────────
        info_fig = plt.figure(figsize=page_size)
        info_fig.patch.set_facecolor(COLOR_BG)
        info_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        _draw_page_template(
            info_fig,
            title="Камера-обскура (Pinhole projection)",
            page_size=page_size,
        )

        _draw_task_block(info_fig, tasks, y_start=0.845, block_gap=0.165)

        if resolved_logo_path:
            add_logo_to_figure(info_fig, resolved_logo_path, logo_position)
        if footer_text:
            add_footer_text(info_fig, footer_text, text_position)

        pdf.savefig(info_fig, pad_inches=0.25, dpi=dpi)
        plt.close(info_fig)

        # ── Chart page ─────────────────────────────────────────────────────
        original_size = fig.get_size_inches().copy()
        original_ax_positions = [ax.get_position().frozen() for ax in fig.axes]
        fig.set_size_inches(page_size, forward=False)
        fig.patch.set_facecolor(COLOR_BG)

        left, bottom, right, top = chart_margins
        width = 1 - left - right
        height = 1 - bottom - top
        if width > 0 and height > 0:
            for ax in fig.axes:
                ax.set_position((left, bottom, width, height))

        if resolved_logo_path:
            add_logo_to_figure(fig, resolved_logo_path, logo_position)
        if footer_text:
            add_footer_text(fig, footer_text, text_position)

        pdf.savefig(fig, pad_inches=0.5, dpi=dpi, orientation="landscape")

        for ax, pos in zip(fig.axes, original_ax_positions):
            ax.set_position(pos)
        fig.set_size_inches(original_size, forward=False)

    logger.info(f"Skychart saved as PDF '{filename}'")


def save_figure_skychart(
    fig: plt.Figure,
    filename: str,
    config: "StereoProjConfig | None" = None,
    local_time: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_name: str | None = None,
    logo_path: str | None = None,
    footer_text: str | None = None,
    dpi: int = 300,
    logo_position: tuple[float, float] = LOGO_POSITION,
    text_position: tuple[float, float] = (0.5, 0.02),
    page_size: tuple[float, float] = (8.27, 11.69),
    # Margins: (left, bottom, right, top) as figure fractions.
    # left=right=0.03 → ~2.5 mm side padding on A4, maximising circle diameter.
    # The chart is square; on portrait A4 the limiting dimension is width.
    # Usable width fraction = 0.94  →  0.94 × 8.27" ≈ 7.77" physical.
    # Same physical size as height → height_frac = 7.77 / 11.69 ≈ 0.665.
    # bottom=0.20 keeps room for footer + label ticks; top=0.135.
    chart_margins: tuple[float, float, float, float] = (
        0.03,
        0.20,
        0.03,
        0.135,
    ),
    print_skychart_info=True,
):
    """
    Save stereographic skychart as a multi-page PDF.
    Page 1 — task sheet with styled header and descriptions.
    Page 2 — the skychart itself, maximised to fill the page width.
    """
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    generation_time = datetime.now()
    if config is not None:
        observation_time = config.local_time
        latitude = float(np.rad2deg(config.latitude))
        longitude = float(np.rad2deg(config.longitude))
    else:
        observation_time = local_time or generation_time

    resolved_logo_path = _resolve_logo(logo_path)

    # ── Tasks definition for stereographic skychart ───────────────────────
    tasks = [
        {
            "label": "Обозначьте зенит и стороны света",
            "description": (
                "Зенит Z ,"
                "стороны горизонта: N (север), E (восток),"
                "S (юг), W (запад)."
            ),
        },
        {
            "label": "Полюс мира и небесный меридиан",
            "description": (
                "Полюс мира P лежит на оси вращения Земли."
                "Для северного полушария\n"
                "он близок к Полярной звезде (α UMi). Небесный меридиан —\n"
                "большой круг через Z, P, N и S."
            ),
        },
        {
            "label": "Проведите эклиптику",
            "description": (
                "Эклиптика — путь Солнца за год,"
                "наклонена к экватору на ε ≈ 23°26′.\n"
                "В стереографической проекции она изображается окружностью\n"
                "или дугой большого круга."
            ),
        },
        {
            "label": "Проведите небесный экватор",
            "description": (
                "Небесный экватор перпендикулярен оси P–Z."
                "В стереографической\n"
                "проекции он тоже является окружностью. Угол между ним и\n"
                "горизонтом равен (90° − φ), где φ — широта наблюдателя."
            ),
        },
        {
            "label": "Обозначьте точку равноденствия",
            "description": (
                "Точка весеннего равноденствия (Овен) или осеннего (Весы) —\n"
                "пересечение эклиптики с экватором."
                "Нанесите ту, что попадает\nв поле зрения карты."
            ),
        },
        {
            "label": "Вычислите звёздное время S",
            "description": ("Запишите результат: " + "_ " * 12),
        },
        {
            "label": "Определите широту наблюдателя φ",
            "description": (
                "Обратите внимание, что"
                "карта дана в стереографической проекции\n"
                "Запишите ответ: " + "_ " * 14
            ),
        },
        {
            "label": "Обозначьте созвездия",
            "description": (
                "Подпишите все видимые созвездия трёхбуквенными латинскими\n"
                "сокращениями (Ori, UMa, Cas…) и проведите их контуры,\n"
                "соединив главные звёзды линиями."
            ),
        },
    ]

    with PdfPages(filename) as pdf:
        plt.rcParams["font.family"] = "monospace"

        # ── Info / task page ───────────────────────────────────────────────
        info_fig = plt.figure(figsize=page_size)
        info_fig.patch.set_facecolor(COLOR_BG)
        info_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        _draw_page_template(
            info_fig,
            title="Стереографическая карта звёздного неба",
            page_size=page_size,
        )

        _draw_task_block(info_fig, tasks, y_start=0.855, block_gap=0.090)

        # ── Observation info block ─────────────────────────────────────────
        if print_skychart_info:
            info_lines: list[str] = [
                f"Время наблюдения : "
                f"{observation_time.strftime('%Y-%m-%d  %H:%M:%S')}",
                f"Звёздное время   : "
                f"{
                    get_sidereal_time(
                        longitude=longitude, local=observation_time
                    )
                }",
            ]
            if latitude is not None and longitude is not None:
                loc = f"{latitude:.2f}°,  {longitude:.2f}°"
                prefix = (
                    f"Место            : {location_name}  ({loc})"
                    if location_name
                    else f"Координаты       : {loc}"
                )
                info_lines.append(prefix)
            elif location_name:
                info_lines.append(f"Место            : {location_name}")

            # Light info box
            n = len(info_lines)
            box_h = 0.015 + 0.024 * n
            box_ax = info_fig.add_axes([0.06, 0.06, 0.88, box_h], zorder=4)
            box_ax.set_xlim(0, 1)
            box_ax.set_ylim(0, 1)
            box_ax.axis("off")
            box_ax.add_patch(
                FancyBboxPatch(
                    (0, 0),
                    1,
                    1,
                    boxstyle="round,pad=0.04",
                    facecolor="#EEF4FB",
                    edgecolor=COLOR_ACCENT,
                    linewidth=0.8,
                    transform=box_ax.transAxes,
                )
            )
            for j, line in enumerate(info_lines):
                box_ax.text(
                    0.03,
                    0.85 - j * (0.9 / max(n, 1)),
                    line,
                    fontsize=9,
                    va="top",
                    color=COLOR_PRIMARY,
                    fontfamily="monospace",
                    transform=box_ax.transAxes,
                )

        if resolved_logo_path:
            add_logo_to_figure(info_fig, resolved_logo_path, logo_position)
        if footer_text:
            add_footer_text(info_fig, footer_text, text_position)

        pdf.savefig(info_fig, pad_inches=0.25, dpi=dpi)
        plt.close(info_fig)

        # ── Chart page ─────────────────────────────────────────────────────
        original_size = fig.get_size_inches().copy()
        original_ax_positions = [ax.get_position().frozen() for ax in fig.axes]
        fig.set_size_inches(page_size, forward=False)
        fig.patch.set_facecolor(COLOR_BG)

        left, bottom, right, top = chart_margins
        width = 1.0 - left - right
        height = 1.0 - bottom - top

        # Force a square axes region so the circular chart never distorts.
        # On portrait A4 the physical width is narrower, so width is the
        # limiting dimension.  Convert width to the equivalent height fraction.
        page_w, page_h = page_size
        square_height_frac = width * page_w / page_h  # same inches as width

        if square_height_frac < height:
            v_centre = bottom + height / 2.0
            height = square_height_frac
            bottom = v_centre - height / 2.0

        if width > 0 and height > 0:
            for ax in fig.axes:
                ax.set_position((left, bottom, width, height))

        if footer_text:
            add_footer_text(fig, footer_text, text_position)

        pdf.savefig(fig, pad_inches=0.25, dpi=dpi)

        # Restore original figure state
        for ax, pos in zip(fig.axes, original_ax_positions):
            ax.set_position(pos)
        fig.set_size_inches(original_size, forward=False)

    logger.info(f"Skychart saved as PDF '{filename}'")


# ─── Internal helpers ────────────────────────────────────────────────────────


def _resolve_logo(logo_path: str | None) -> str | None:
    """Resolve logo path, falling back to the bundled logo_astrageek.png."""
    if logo_path is None:
        default_logo = Path(__file__).resolve().parent / "logo_astrageek.png"
        return str(default_logo) if default_logo.exists() else None

    p = Path(logo_path)
    if p.is_absolute():
        return str(p) if p.exists() else None

    candidates = [
        Path(__file__).resolve().parent / p,
        Path(__file__).resolve().parents[2] / p,
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None
