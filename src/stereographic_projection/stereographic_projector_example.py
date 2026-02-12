from src.hip_catalog.hip_catalog import CatalogConstraints, Catalog
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.stereographic_projection.stereographic_projector import StereoProjector, StereoProjConfig, ConstellationConfig
from src.helpers.pdf_helpers.figure2pdf import save_figure_skychart
from datetime import datetime


def main():
    # Configure catalog
    constraints = CatalogConstraints(
        max_magnitude=5.5,
    )

    # Configure projection: date, time and place
    config = StereoProjConfig(
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=False,
        add_planets=False,
        add_ticks=False,
        add_horizontal_grid=False,
        add_equatorial_grid=True,
        add_zenith=False,
        add_poles=False,
        add_constellations=True,
        add_constellations_names=True,
        grid_theta_step=15.0,
        grid_phi_step=15.0,
        random_origin=False,
        local_time=datetime(
            year=2026,
            month=2,
            day=11,
            hour=0,
            minute=0,
            second=0,
        ),
        latitude=90,
        longitude=180,
    )

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellation_linewidth=0.5,
        constellation_alpha=0.5,
    )

    # Create catalog object (without data)
    catalog = Catalog(
        catalog_name='hip_data.tsv',
        use_cache=True,
    )

    # Create projector object with configuration
    proj = StereoProjector(
        config=config,
        catalog=catalog,
        planets_catalog=PlanetCatalog(),
        constellation_config=constellation_config,
    )

    # Make figure with constrains
    fig, ax = proj.generate(constraints=constraints)

    # Save skychart
    save_figure_skychart(
        fig=fig,
        filename="polar_scatter_local_logo.pdf",
        config=config,
        location_name="",
        logo_path="helpers/pdf_helpers/logo_astrageek.png",
        footer_text="Generate more on skychart.astrageek.ru.",
        logo_position=(0.12, 0.97),
        text_position=(0.5, 0.01),
        print_skychart_info=False,
    )

if __name__ == "__main__":
    main()