from sqlalchemy.dialects.mssql.information_schema import constraints

from stereographic_projection.stereographic_projector import StereoProjector, StereoProjConfig
from stereographic_projection.hip_catalog.hip_catalog import NumpyCatalog, CatalogConstraints
from stereographic_projection.helpers.pdf_helpers.figure2pdf import save_figure
import matplotlib.pyplot as plt
from datetime import datetime

def stars_with_logo(figure: plt.Figure, need_pdf: bool = False):
    """
    Example with local logo file.

    :param figure: projection figure to plot
    :param need_pdf: enable / disable pdf saving
    """

    footer = "© 2025 AstraGeek. All rights reserved."

    if need_pdf:
        save_figure(
            fig=figure,
            filename="polar_scatter_local_logo.pdf",
            logo_path="./helpers/pdf_helpers/logo_astrageek.png",
            footer_text=footer,
            logo_position=(0.15, 0.97),
            text_position=(0.5, 0.01),
        )

    plt.show()


if __name__ == "__main__":

    # Configure catalog
    constraints = CatalogConstraints(
        max_magnitude=8.0,
        dec_range=(45.0, 90.0),
    )

    # Configure projection: date, time and place
    config = StereoProjConfig(
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        local_time=datetime(
            year=2025,
            month=9,
            day=1,
            hour=22,
            minute=20,
            second=40
        ),
        latitude=45.0,
        longitude=0.0
    )

    # Create catalog object (without data)
    catalog = NumpyCatalog(
        catalog_name='hip_data.tsv',
        cache_dir='cache',
        use_cache=True
    )

    # Create projector object with configuration
    proj = StereoProjector(
        config=config,
        catalog=catalog
    )

    # Make figure with constrains
    figure = proj.generate(constraints=constraints)

    # Plot figure
    stars_with_logo(figure, need_pdf=False)