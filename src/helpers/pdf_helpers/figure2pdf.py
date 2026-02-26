"""Module with function that creates pdf from a given plt.figure."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image

from src.helpers.time.time import get_sidereal_time

if TYPE_CHECKING:
    from src.stereographic_projection.stereographic_projector import (
        StereoProjConfig,
    )


# ── Palette ──────────────────────────────────────────────────────────────────
COLOR_TEXT = "#1A1A1A"
COLOR_MUTED = "#555555"
COLOR_RULE = "#AAAAAA"
COLOR_BG = "#FFFFFF"

LOGO_ZOOM = 0.10
LOGO_POS = (0.02, 0.97)  # top-left corner of task page only


# ── Internal helpers ─────────────────────────────────────────────────────────


def _resolve_logo(logo_path: str | None) -> str | None:
    if logo_path is None:
        default = Path(__file__).resolve().parent / "logo_astrageek.png"
        return str(default) if default.exists() else None
    p = Path(logo_path)
    if p.is_absolute():
        return str(p) if p.exists() else None
    for base in (
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parents[2],
    ):
        candidate = base / p
        if candidate.exists():
            return str(candidate)
    return None


def add_logo_to_figure(
    fig: plt.Figure,
    logo_path: str | None = None,
    position: tuple[float, float] = LOGO_POS,
    size: float = LOGO_ZOOM,
):
    """
    Add a logo to the figure.

    :param fig: Figure to be saved
    :type fig: plt.Figure
    :param logo_path: path to the logo
    :type logo_path: str | None
    :param position: position, where to draw
    :type position: tuple[float, float]
    :param size: relative size for the logo
    :type size: float
    """
    try:
        logo = Image.open(logo_path)
        im = OffsetImage(np.array(logo), zoom=size)
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
    fontsize: int = 9,
    color: str = COLOR_MUTED,
):
    """
    Add footer text to the figure.

    :param fig: Figure to be saved
    :type fig: plt.Figure
    :param text: text to be written
    :type text: str
    :param position: position, where to draw
    :type position: tuple[float, float]
    :param fontsize: fontsize of the text
    :type fontsize: int
    :param color: color of the text
    :type color: str
    """
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


def _hline(
    fig: plt.Figure,
    y: float,
    x0: float = 0.07,
    x1: float = 0.93,
    color: str = COLOR_RULE,
    lw: float = 0.6,
):
    ax = fig.add_axes([x0, y, x1 - x0, 0.001], zorder=3)
    ax.set_facecolor(color)
    ax.axis("off")


def _answer_line(width_chars: int = 28) -> str:
    """
    Return a fixed-width answer blank using Unicode underscore characters.
    """
    return "\u00a0" + ("\u2005" + "\u0332" + "\u00a0") * width_chars


def _draw_header(
    fig: plt.Figure,
    title: str,
    logo_path: str | None = None,
    page_size: tuple[float, float] = (8.27, 11.69),
):
    """
    Draw title on the right side, logo on the left.
    Title is offset right so it never overlaps the logo.
    """
    # Logo in top-left
    if logo_path:
        add_logo_to_figure(fig, logo_path, position=LOGO_POS, size=LOGO_ZOOM)

    # Title starts well to the right of the logo area (~20% from left)
    fig.text(
        0.22,
        0.955,
        title,
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXT,
        va="top",
        fontfamily="monospace",
    )
    _hline(fig, y=0.930)


def _draw_task_block(
    fig: plt.Figure,
    tasks: list[dict],
    y_start: float = 0.910,
    x_left: float = 0.07,
    label_fontsize: int = 10,
    desc_fontsize: int = 8.5,
    block_gap: float = 0.058,  # tighter than before
):
    """
    Draw numbered task list.
    Format:  "1.  Label text  ▢"
    Description on next line, indented, italic grey.
    """
    y = y_start
    for i, task in enumerate(tasks, 1):
        label_line = f"{i}.  {task['label']}  \u25a2"
        fig.text(
            x_left,
            y,
            label_line,
            fontsize=label_fontsize,
            va="top",
            color=COLOR_TEXT,
            fontfamily="monospace",
            fontweight="bold",
        )
        if task.get("description"):
            fig.text(
                x_left + 0.035,
                y - 0.026,
                task["description"],
                fontsize=desc_fontsize,
                va="top",
                color=COLOR_MUTED,
                fontfamily="monospace",
                style="italic",
            )
        y -= block_gap


# ── Public save functions ────────────────────────────────────────────────────


def save_figure(
    fig: plt.Figure,
    filename: str,
    logo_path: str | None = None,
    footer_text: str | None = None,
    dpi: int = 300,
    logo_position: tuple[float, float] = LOGO_POS,
    text_position: tuple[float, float] = (0.5, 0.02),
):
    """
    Save figure as PDF with logo and footer text.

    :param filename: Name of the file where to save a fig
    :type filename: str
    :param fig: Figure to be saved
    :type fig: plt.Figure
    :param logo_path: path to the logo
    :type logo_path: str | None
    :param footer_text: text to be written
    :type footer_text: str | None
    :param logo_position: position, where to draw logo
    :type logo_position: tuple[float, float]
    :param text_position: position, where to write text
    :type text_position: tuple[float, float]
    :param dpi: dots per inch
    :type dpi: int
    """
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
    logo_position: tuple[float, float] = LOGO_POS,
    text_position: tuple[float, float] = (0.5, 0.02),
    page_size: tuple[float, float] = (11.69, 8.27),
    chart_margins: tuple[float, float, float, float] = (0.1, 0.2, 0.1, 0.1),
):
    """
    Save figure as PDF with logo and footer text (pinhole projection result).

    :param filename: Name of the file where to save a fig
    :type filename: str
    :param fig: Figure to be saved
    :type fig: plt.Figure
    :param logo_path: path to the logo
    :type logo_path: str | None
    :param footer_text: text to be written
    :type footer_text: str | None
    :param logo_position: position, where to draw logo
    :type logo_position: tuple[float, float]
    :param text_position: position, where to write text
    :type text_position: tuple[float, float]
    :param dpi: dots per inch
    :type dpi: int
    :param page_size: size of output page
    :type page_size: tuple[float, float]
    :param chart_margins: side margins
    :type chart_margins: tuple[float, float, float, float]
    """
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    resolved_logo = _resolve_logo(logo_path)

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
                "Эклиптика — видимый путь Солнца среди звёзд "
                "(наклонена к экватору\n"
                "на ε ≈ 23°26′). Нанесите её, "
                "если она попадает в поле зрения снимка."
            ),
        },
        {
            "label": "Проведите небесный экватор",
            "description": (
                "Небесный экватор — проекция земного экватора "
                "на небесную сферу.\n"
                "Нанесите его дугой, если он присутствует на снимке."
            ),
        },
        {
            "label": "Обозначьте точку равноденствия",
            "description": (
                "Нанесите точки осеннего или весеннего равноденствия, "
                "если они видны.\n"
                "Это точки пересечения эклиптики с небесным экватором."
            ),
        },
    ]

    with PdfPages(filename) as pdf:
        plt.rcParams["font.family"] = "monospace"

        # ── Task page (landscape) ──────────────────────────────────────────
        info_fig = plt.figure(figsize=page_size)
        info_fig.patch.set_facecolor(COLOR_BG)
        info_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        _draw_header(
            info_fig,
            title="Камера-обскура  (Pinhole projection)",
            logo_path=resolved_logo,
            page_size=page_size,
        )
        _draw_task_block(info_fig, tasks, y_start=0.895, block_gap=0.180)

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
    logo_position: tuple[float, float] = LOGO_POS,
    text_position: tuple[float, float] = (0.5, 0.02),
    page_size: tuple[float, float] = (8.27, 11.69),
    chart_margins: tuple[float, float, float, float] = (
        0.075,
        0.25,
        0.075,
        0.1,
    ),
    print_skychart_info: bool = True,
):
    """
    Save stereographic skychart as a two-page PDF.
    Page 1 — task sheet.  Page 2 — the skychart itself.

    :param fig: Figure to be saved
    :type fig: plt.Figure
    :param filename: output file name (pdf extension added if missing)
    :type filename: str
    :param config: stereographic projector config (optional)
    :type config: StereoProjConfig | None
    :param local_time: observation time (used when config is None)
    :type local_time: datetime | None
    :param latitude: observer latitude in degrees
    :type latitude: float | None
    :param longitude: observer longitude in degrees
    :type longitude: float | None
    :param location_name: human-readable location name
    :type location_name: str | None
    :param logo_path: path to logo image
    :type logo_path: str | None
    :param footer_text: footer string
    :type footer_text: str | None
    :param dpi: output resolution
    :type dpi: int
    :param logo_position: figure-fraction (x, y) for logo anchor
    :type logo_position: tuple[float, float]
    :param text_position: figure-fraction (x, y) for footer text
    :type text_position: tuple[float, float]
    :param page_size: figure size in inches (width, height)
    :type page_size: tuple[float, float]
    :param chart_margins: (left, bottom, right, top) as figure fractions
    :type chart_margins: tuple[float, float, float, float]
    :param print_skychart_info: whether to include observation info block
    :type print_skychart_info: bool
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

    resolved_logo = _resolve_logo(logo_path)

    tasks = [
        {
            "label": "Обозначьте зенит и стороны света",
            "description": (
                "Зенит Z, стороны горизонта: N (север), E (восток), "
                "S (юг), W (запад)."
            ),
        },
        {
            "label": "Полюс мира и небесный меридиан",
            "description": (
                "Полюс мира P лежит на оси вращения Земли. "
                "Для северного полушария\n"
                "он близок к Полярной звезде (α UMi). Небесный меридиан —\n"
                "большой круг через Z, P, N и S."
            ),
        },
        {
            "label": "Проведите эклиптику",
            "description": (
                "Эклиптика — путь Солнца за год, "
                "наклонена к экватору на ε ≈ 23°26′.\n"
                "В стереографической проекции она изображается окружностью\n"
                "или дугой большого круга."
            ),
        },
        {
            "label": "Проведите небесный экватор",
            "description": (
                "Небесный экватор перпендикулярен оси P–Z. "
                "В стереографической\n"
                "проекции он тоже является окружностью. Угол между ним и\n"
                "горизонтом равен (90° − φ), где φ — широта наблюдателя."
            ),
        },
        {
            "label": "Обозначьте точку равноденствия",
            "description": (
                "Точка весеннего равноденствия (Овен ♈) или "
                "осеннего (Весы ♎) —\n"
                "пересечение эклиптики с экватором. "
                "Нанесите ту, что попадает\n"
                "в поле зрения карты."
            ),
        },
        {
            "label": "Вычислите звёздное время S",
            "description": "Ответ: _______________________________",
        },
        {
            "label": "Определите широту наблюдателя φ",
            "description": (
                "Обратите внимание: карта дана в стереографической проекции.\n"
                "Ответ: _______________________________"
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

        # ── Task page ──────────────────────────────────────────────────────
        info_fig = plt.figure(figsize=page_size)
        info_fig.patch.set_facecolor(COLOR_BG)
        info_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        _draw_header(
            info_fig,
            title="Стереографическая карта звёздного неба",
            logo_path=resolved_logo,
            page_size=page_size,
        )
        _draw_task_block(info_fig, tasks, y_start=0.908, block_gap=0.088)

        # ── Observation info ───────────────────────────────────────────────
        if print_skychart_info:
            info_lines: list[str] = [
                f"Время наблюдения : {
                    observation_time.strftime('%Y-%m-%d  %H:%M:%S')
                }",
                f"Звёздное время   : {
                    get_sidereal_time(
                        longitude=longitude, local=observation_time
                    )
                }",
            ]
            if latitude is not None and longitude is not None:
                loc = f"{latitude:.2f}°,  {longitude:.2f}°"
                if location_name:
                    info_lines.append(
                        f"Место            : {location_name}  ({loc})"
                    )
                else:
                    info_lines.append(f"Координаты       : {loc}")
            elif location_name:
                info_lines.append(f"Место            : {location_name}")

            _hline(info_fig, y=0.110)
            y_info = 0.100
            for line in reversed(info_lines):
                info_fig.text(
                    0.07,
                    y_info,
                    line,
                    fontsize=8.5,
                    color=COLOR_MUTED,
                    va="bottom",
                    fontfamily="monospace",
                )
                y_info += 0.021

        if footer_text:
            add_footer_text(info_fig, footer_text, text_position)

        pdf.savefig(info_fig, pad_inches=0.25, dpi=dpi)
        plt.close(info_fig)

        # ── Chart page ─────────────────────────────────────────────────────
        original_size = fig.get_size_inches().copy()
        original_ax_positions = [ax.get_position().frozen() for ax in fig.axes]
        fig.set_size_inches(page_size, forward=False)
        fig.patch.set_facecolor(COLOR_BG)

        left, bottom, right, top_m = chart_margins
        width = 1.0 - left - right
        height = 1.0 - bottom - top_m

        phys_w, phys_h = page_size
        side = min(width * phys_w, height * phys_h)
        sq_w = side / phys_w
        sq_h = side / phys_h
        cx = left + width / 2
        cy = bottom + height / 2
        ax_l = cx - sq_w / 2
        ax_b = cy - sq_h / 2

        for ax in fig.axes:
            ax.set_position((ax_l, ax_b, sq_w, sq_h))

        pdf.savefig(fig, pad_inches=0.25, dpi=dpi)

        for ax, pos in zip(fig.axes, original_ax_positions):
            ax.set_position(pos)
        fig.set_size_inches(original_size, forward=False)

    logger.info(f"Skychart saved as PDF '{filename}'")
