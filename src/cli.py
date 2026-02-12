import click
import sys
from pathlib import Path
import tomllib

from datetime import datetime

from src.helpers.pdf_helpers.figure2pdf import save_figure_skychart
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.stereographic_projection.stereographic_projector import StereoProjConfig, ConstellationConfig, StereoProjector


# ==================== ОСНОВНАЯ CLI ГРУППА ====================

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Подробный вывод')
@click.pass_context
def cli(ctx, verbose):
    """🌌 AstraGeek - инструмент для построения звездных карт"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    if verbose:
        click.echo("✅ Режим подробного вывода включен")


# ==================== КОМАНДА STEREOGRAPHIC ====================

@cli.command('stereographic')
@click.option('--add_ecliptic', is_flag=True, help='Add ecliptic to the chart', default=False)
@click.option('--add_equator', is_flag=True, help='Add equator to the chart', default=False)
@click.option('--add_galactic_equator', is_flag=True, help='Add galactic equator to the chart', default=False)
@click.option('--add_planets', is_flag=True, help='Add planets to the chart', default=False)
@click.option('--add_ticks', is_flag=True, help='Add ticks to the chart', default=False)
@click.option('--add_horizontal_grid', is_flag=True, help='Add horizontal grid to the chart', default=False)
@click.option('--add_equatorial_grid', is_flag=True, help='Add equatorial grid to the chart', default=False)
@click.option('--add_zenith', is_flag=True, help='Add zenith to the chart', default=False)
@click.option('--add_poles', is_flag=True, help='Add poles to the chart', default=False)
@click.option('--add_constellations', is_flag=True, help='Add constellations to the chart', default=False)
@click.option('--grid_theta_step', type=float, help='Theta step for grid in degrees', default=15.0)
@click.option('--grid_phi_step', type=float, help='Phi step for grid in degrees',default=15.0)
@click.option('--random_origin', is_flag=True, help='Use random origin for projection', default=False)
@click.option('--local_time', type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']),
              help='Local time (default: 2004-06-14 15:10:00)', default='2004-06-14 15:10:00')
@click.option('--latitude', type=float, help='Observer latitude in degrees (default: 45)', default=45.0)
@click.option('--longitude', type=float, help='Observer longitude in degrees (default: 0)', default=0.0)
@click.option('--magnitude', type=float, help='Observer maximum visual magnitude (default: 5.5)', default=5.5)
@click.option('--output', type=click.Path(), help='Output file for the skychart', default='polar_scatter_local_logo.pdf')
@click.pass_context
def stereographic(ctx, add_ecliptic, add_equator, add_galactic_equator,
                  add_planets, add_ticks, add_horizontal_grid,
                  add_equatorial_grid, add_zenith, add_poles, add_constellations,
                  grid_theta_step, grid_phi_step, random_origin, local_time,
                  latitude, longitude, magnitude, output):
    try:
        # Extract parameters with defaults
        if local_time is None:
            local_time = datetime(2004, 6, 14, 15, 10, 0)

        config = StereoProjConfig(
            add_ecliptic=add_ecliptic,
            add_equator=add_equator,
            add_galactic_equator=add_galactic_equator,
            add_planets=add_planets,
            add_ticks=add_ticks,
            add_horizontal_grid=add_horizontal_grid,
            add_equatorial_grid=add_equatorial_grid,
            add_zenith=add_zenith,
            add_poles=add_poles,
            add_constellations=add_constellations,
            grid_theta_step=grid_theta_step,
            grid_phi_step=grid_phi_step,
            random_origin=random_origin,
            local_time=local_time,
            latitude=latitude,
            longitude=longitude,
        )

        # Configure catalog
        constraints = CatalogConstraints(
            max_magnitude=magnitude,
        )

        # Constellation viewing configurations
        constellation_config = ConstellationConfig()

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
            filename=output,
            config=config,
            location_name="",
            logo_path="helpers/pdf_helpers/logo_astrageek.png",
            footer_text="Generate more on skychart.astrageek.ru.",
            logo_position=(0.12, 0.97),
            text_position=(0.5, 0.01),
            print_skychart_info=False,
        )
        click.echo(f"✅ Карта успешно создана: {output}")

    except Exception as e:
        click.echo(f"❌ Ошибка при генерации карты: {e}", err=True)
        sys.exit(1)


# ==================== КОМАНДА PINHOLE ====================

@cli.command()
@click.argument('constellation', type=str)
@click.option('--fov', type=float, default=60.0,
              help='Поле зрения в градусах (по умолчанию: 60)')
@click.option('--rotation', type=float, default=0.0,
              help='Угол поворота камеры в градусах (по умолчанию: 0)')
@click.option('--width', type=int, default=800,
              help='Ширина изображения в пикселях (по умолчанию: 800)')
@click.option('--height', type=int, default=600,
              help='Высота изображения в пикселях (по умолчанию: 600)')
@click.option('--grid/--no-grid', default=True,
              help='Показать координатную сетку (включено по умолчанию)')
@click.option('--output', '-o', default=None,
              help='Путь для сохранения изображения (по умолчанию: созвездие_название.png)')
@click.pass_context
def pinhole(ctx, constellation, fov, rotation, width, height, grid, output):
    """🔭 Создать карту области неба вокруг созвездия (pinhole projection)"""

    if output is None:
        output = f"{constellation.lower()}_map.png"

    if ctx.obj.get('verbose'):
        click.echo(f"🔄 Начинаю генерацию pinhole-проекции...")
        click.echo(f"✨ Созвездие: {constellation}")
        click.echo(f"👁️ Поле зрения: {fov}°")
        click.echo(f"🔄 Поворот: {rotation}°")
        click.echo(f"📐 Размер: {width}x{height}")
        click.echo(f"📊 Сетка: {'включена' if grid else 'выключена'}")
        click.echo(f"💾 Сохранение в: {output}")

    try:
        from astrageek.pinhole_projection import generate as generate_pinhole
    except ImportError as e:
        click.echo(f"❌ Ошибка импорта модуля pinhole_projection: {e}", err=True)
        click.echo("🔧 Убедитесь, что модуль существует и установлены все зависимости")
        sys.exit(1)

    try:
        result = generate_pinhole(
            constellation_name=constellation,
            fov_degrees=fov,
            rotation_angle=rotation,
            image_width=width,
            image_height=height,
            show_grid=grid,
            output_file=output
        )

        click.echo(f"✅ Pinhole-карта успешно создана: {output}")
        if ctx.obj.get('verbose'):
            click.echo(f"📊 Созвездие центрировано на: RA {result.get('ra', 0):.2f}°, "
                       f"Dec {result.get('dec', 0):.2f}°")

    except Exception as e:
        click.echo(f"❌ Ошибка при генерации pinhole-карты: {e}", err=True)
        sys.exit(1)


# ==================== КОМАНДА CONSTELLATIONS ====================

@cli.command()
@click.option('--list', 'list_constellations', is_flag=True,
              help='Показать все доступные созвездия')
@click.option('--search', type=str,
              help='Поиск созвездий по названию (регистр не учитывается)')
@click.argument('constellation', type=str, required=False)
@click.pass_context
def constellations(ctx, list_constellations, search, constellation):
    """✨ Работа с созвездиями (список, поиск, информация)"""

    try:
        from astrageek.constellations_metadata import get_constellations
    except ImportError:
        # Заглушка, если модуль еще не реализован
        constellations_data = {
            "Orion": {"name": "Орион", "abbr": "Ori", "season": "Зима"},
            "Ursa Major": {"name": "Большая Медведица", "abbr": "UMa", "season": "Круглогодично"},
            "Cassiopeia": {"name": "Кассиопея", "abbr": "Cas", "season": "Осень"},
        }
    else:
        constellations_data = get_constellations()

    if list_constellations:
        click.echo("📋 Список доступных созвездий (88):")
        for i, (key, data) in enumerate(constellations_data.items(), 1):
            name = data.get('name', key)
            click.echo(f"  {i:2d}. {key:20} ({name})")
        return

    if search:
        click.echo(f"🔍 Результаты поиска '{search}':")
        found = False
        for key, data in constellations_data.items():
            if search.lower() in key.lower() or search.lower() in data.get('name', '').lower():
                name = data.get('name', key)
                click.echo(f"  • {key} ({name}) - {data.get('season', 'сезон неизвестен')}")
                found = True

        if not found:
            click.echo("  😕 Созвездий не найдено")
        return

    if constellation:
        const_data = constellations_data.get(constellation)
        if const_data:
            click.echo(f"✨ Информация о созвездии '{constellation}':")
            click.echo(f"  📛 Название: {const_data.get('name', constellation)}")
            click.echo(f"  🔤 Аббревиатура: {const_data.get('abbr', '—')}")
            click.echo(f"  🗺️  Сезон видимости: {const_data.get('season', '—')}")
            click.echo(f"  🌟 Ярчайшая звезда: {const_data.get('brightest_star', '—')}")
        else:
            click.echo(f"❌ Созвездие '{constellation}' не найдено")
            click.echo(f"ℹ️  Используйте 'astrageek constellations --list' для просмотра всех созвездий")
        return

    # Если не указаны аргументы, показываем справку
    click.echo("ℹ️  Используйте одну из опций:")
    click.echo("  • --list - показать все созвездия")
    click.echo("  • --search <текст> - найти созвездия по названию")
    click.echo("  • <название> - информация о конкретном созвездии")



# ==================== ТОЧКА ВХОДА ====================

if __name__ == '__main__':
    cli()