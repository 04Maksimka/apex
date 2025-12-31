"""Module with function that creates pdf from a given plt.figure."""
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from loguru import logger
from PIL import Image
from helpers.time.time import get_sidereal_time

if TYPE_CHECKING:
    from stereographic_projection.stereographic_projector import StereoProjConfig


def add_logo_to_figure(
    fig: plt.Figure,
    logo_path: str | None = None,
    position: tuple[float, float] = (0.02, 0.95),
    size: float = 0.2,
) -> None:
    """Add a logo to the figure.

    :param fig: Figure to be saved
    :param logo_path: path to the logo
    :param position: position, where to draw
    :param size: relative size for the logo
    """
    try:
        logo = Image.open(logo_path)
        # Convert to array for matplotlib
        logo_array = np.array(logo)
        # Create OffsetImage
        im = OffsetImage(logo_array, zoom=size)
        # Create AnnotationBbox
        ab = AnnotationBbox(
            im,
            position,
            xycoords='figure fraction',
            frameon=False,
            box_alignment=(0, 1),
        )
        # Add to figure
        fig.add_artist(ab)

    except Exception as e:
        print(f"Error loading logo: {e}")


def add_footer_text(
    fig: plt.Figure,
    text: str,
    position: tuple[float, float] = (0.5, 0.02),
    fontsize: int = 9 ,
    color: str = 'gray',
):
    """Add footer text to the figure.

    :param fig: Figure to be saved
    :param text: text to be written
    :param position: position, where to draw
    :param fontsize: fontsize of the text
    :param color: color of the text
    """
    fig.text(
        position[0], position[1], text,
        fontsize=fontsize, color=color,
        ha='center', va='bottom',
        transform=fig.transFigure,
    )


def save_figure(
    fig: plt.Figure,
    filename: str,
    logo_path: str | None = None,
    footer_text: str | None = None,
    dpi: int = 300,
    logo_position: tuple[float, float] = (0.02, 0.95),
    text_position: tuple[float, float] = (0.5, 0.02),

):
    """Save figure as PDF with logo and footer text.

    :param filename: Name of the file where to save a fig
    :param fig: Figure to be saved
    :param logo_path: path to the logo
    :param footer_text: text to be written
    :param logo_position: position, where to draw logo
    :param text_position: position, where to draw logo
    :param dpi: dots per inch
    """
    if logo_path:
        add_logo_to_figure(fig, logo_path, logo_position)

    if footer_text:
        add_footer_text(fig, footer_text, text_position)

    if not filename.endswith('.pdf'):
        filename += '.pdf'

    fig.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    logger.info(f"Figure saved as '{filename}'")


def save_figure_skychart(
    fig: plt.Figure,
    filename: str,
    config: 'StereoProjConfig | None' = None,
    local_time: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_name: str | None = None,
    logo_path: str | None = None,
    footer_text: str | None = None,
    dpi: int = 300,
    logo_position: tuple[float, float] = (0.02, 0.95),
    text_position: tuple[float, float] = (0.5, 0.02),
    page_size: tuple[float, float] = (8.27, 11.69),
    chart_margins: tuple[float, float, float, float] = (0.075, 0.25, 0.075, 0.1),
    print_skychart_info=True,
):
    if not filename.endswith('.pdf'):
        filename += '.pdf'

    generation_time = datetime.now()
    if config is not None:
        observation_time = config.local_time
        latitude = float(np.rad2deg(config.latitude))
        longitude = float(np.rad2deg(config.longitude))
    else:
        observation_time = local_time or generation_time

    resolved_logo_path: str | None = None
    if logo_path is None:
        default_logo = Path(__file__).resolve().parent / 'logo_astrageek.png'
        if default_logo.exists():
            resolved_logo_path = str(default_logo)
    else:
        p = Path(logo_path)
        if p.is_absolute():
            if p.exists():
                resolved_logo_path = str(p)
        else:
            candidates = [
                (Path(__file__).resolve().parent / p),
                (Path(__file__).resolve().parents[2] / p),
            ]
            for c in candidates:
                if c.exists():
                    resolved_logo_path = str(c)
                    break

    with PdfPages(filename) as pdf:
        info_fig = plt.figure(figsize=page_size)
        info_fig.patch.set_facecolor('white')
        info_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        plt.rcParams['font.family'] = 'monospace'

        tasks = [
            '▢ 1. Обозначьте зенит символом $Z$ и стороны света символами $N$, $E$, $S$, $W$.',
            '▢ 2. Обозначьте полюс мира символом $P$ и проведите небесный меридиан.',
            '▢ 3. Проведите небесный экватор и обозначьте точку весеннего\nравноденствия символом ♈'
            ' или точку осеннего равноденствия символом ♎.',
            '▢ 4. Вычислите звездное время $S$ на момент снимка: ' + '_' * 20,
            '▢ 5. Учитывая, что снимок приведен в стереографической проекции,\nопределите широту $\\varphi$ '
            'места наблюдения: ' + '_' * 20,
            '▢ 6. Обозначьте на снимке видимые созвездия их трехбуквенными\nлатинскими наименованиями, проведите контуры этих созвездий.',
        ]

        y = 0.85
        line_step = 0.06
        for t in tasks:
            info_fig.text(0.08, y, t, fontsize=12, va='top')
            y -= line_step

        if print_skychart_info:
            info_lines: list[str] = [
                f"Время наблюдения: {observation_time.strftime('%Y-%m-%d %H:%M:%S')}",
                f'Звездное время: {get_sidereal_time(longitude=longitude, local=observation_time)}'
            ]
            if latitude is not None and longitude is not None:
                loc = f'Широта: {latitude:.1f}$^\\circ$, Долгота: {longitude:.1f}$^\\circ$'
                if location_name:
                    loc = f'Место: {location_name} ({loc})'
                else:
                    loc = f'Место: {loc}'
                info_lines.append(loc)
            elif location_name:
                info_lines.append(f'Место: {location_name}')

            info_fig.text(
                0.08,
                0.16,
                '\n'.join(info_lines),
                fontsize=10,
                va='top',
                color='gray',
            )

        if resolved_logo_path:
            add_logo_to_figure(info_fig, resolved_logo_path, logo_position)
        if footer_text:
            add_footer_text(info_fig, footer_text, text_position)

        pdf.savefig(info_fig, pad_inches=0.25, dpi=dpi)
        plt.close(info_fig)

        original_size = fig.get_size_inches().copy()
        original_ax_positions = [ax.get_position().frozen() for ax in fig.axes]
        fig.set_size_inches(page_size, forward=False)
        fig.patch.set_facecolor('white')

        left, bottom, right, top = chart_margins
        width = 1 - left - right
        height = 1 - bottom - top
        if width > 0 and height > 0:
            for ax in fig.axes:
                ax.set_position((left, bottom, width, height))

        if footer_text:
            add_footer_text(fig, footer_text, text_position)

        pdf.savefig(fig, pad_inches=0.25, dpi=dpi)

        for ax, pos in zip(fig.axes, original_ax_positions):
            ax.set_position(pos)
        fig.set_size_inches(original_size, forward=False)

    logger.info(f"Skychart saved as two-page PDF '{filename}'")
