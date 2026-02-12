"""
Основной CLI модуль для AstraGeek
"""

import sys
from pathlib import Path

import click

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


# ==================== ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ИНФОРМАЦИИ ====================

def get_project_info():
    """Получить информацию о проекте из pyproject.toml"""

    # Способ 1: Если пакет установлен
    try:
        from importlib.metadata import metadata as md, PackageNotFoundError
        try:
            meta = md("astrageek")
            return {
                "name": meta["Name"],
                "version": meta["Version"],
                "description": meta["Summary"],
                "author": meta["Author"],
                "python_version": meta["Requires-Python"],
                "license": meta.get("License", "MIT"),
                "dependencies": [d for d in meta.get_all("Requires-Dist", [])],
                "repo": meta.get("Home-page", "https://github.com/04Maksimka/AstraGeek")
            }
        except PackageNotFoundError:
            pass
    except ImportError:
        pass

    # Способ 2: Чтение файла напрямую
    if tomllib is None:
        return {"error": "Для работы команды установите tomli: pip install tomli"}

    # Ищем pyproject.toml
    current_dir = Path(__file__).parent.parent
    toml_path = current_dir / "pyproject.toml"

    if not toml_path.exists():
        for path in [current_dir, current_dir.parent]:
            if (path / "pyproject.toml").exists():
                toml_path = path / "pyproject.toml"
                break

    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        urls = project.get("urls", {})

        return {
            "name": project.get("name", "astrageek"),
            "version": project.get("version", "0.2.0"),
            "description": project.get("description", ""),
            "author": ", ".join([a.get("name", "") for a in project.get("authors", [])]),
            "python_version": project.get("requires-python", ">=3.9"),
            "license": project.get("license", {}).get("text", "MIT"),
            "dependencies": project.get("dependencies", []),
            "repo": urls.get("Repository", "https://github.com/04Maksimka/AstraGeek")
        }

    return {"error": "pyproject.toml не найден"}


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


# ==================== КОМАНДА INFO ====================

@cli.command()
def info():
    """📊 Показать информацию о проекте"""
    info_data = get_project_info()

    if "error" in info_data:
        click.echo(f"❌ Ошибка: {info_data['error']}", err=True)
        return

    click.echo("=" * 50)
    click.echo(f"🌌 {info_data['name'].upper()} v{info_data['version']}")
    click.echo("=" * 50)
    click.echo(f"📝 {info_data['description']}")
    click.echo(f"👤 Автор(ы): {info_data['author']}")
    click.echo(f"🐍 Python: {info_data['python_version']}")
    click.echo(f"📜 Лицензия: {info_data['license']}")
    click.echo(f"🔗 Репозиторий: {info_data['repo']}")
    click.echo(f"📦 Зависимости ({len(info_data['dependencies'])}):")
    for dep in info_data['dependencies']:
        click.echo(f"  • {dep}")
    click.echo("=" * 50)


# ==================== КОМАНДА STEREOGRAPHIC ====================

@cli.command()
@click.option('--lat', type=float, required=True,
              help='Широта наблюдателя в градусах (-90 до 90)')
@click.option('--lon', type=float, required=True,
              help='Долгота наблюдателя в градусах (-180 до 180)')
@click.option('--time', type=str, required=True,
              help='Время наблюдения в формате YYYY-MM-DD HH:MM')
@click.option('--output', '-o', default='skychart.png',
              help='Путь для сохранения изображения (по умолчанию: skychart.png)')
@click.option('--show-planets', is_flag=True, default=False,
              help='Показать планеты на карте')
@click.option('--show-grid', is_flag=True, default=True,
              help='Показать координатную сетку (включено по умолчанию)')
@click.option('--magnitude', type=float, default=6.0,
              help='Предельная звездная величина (по умолчанию: 6.0)')
@click.pass_context
def stereographic(ctx, lat, lon, time, output, show_planets, show_grid, magnitude):
    """🌍 Создать круговую карту звездного неба (stereographic projection)"""

    if ctx.obj.get('verbose'):
        click.echo(f"🔄 Начинаю генерацию стереографической проекции...")
        click.echo(f"📍 Координаты: {lat}°, {lon}°")
        click.echo(f"⏰ Время: {time}")
        click.echo(f"💾 Сохранение в: {output}")

    # ВАЖНО: Импорт здесь, чтобы избежать циклических зависимостей
    try:
        from astrageek.stereographic_projection import generate
    except ImportError as e:
        click.echo(f"❌ Ошибка импорта модуля stereographic_projection: {e}", err=True)
        click.echo("🔧 Убедитесь, что модуль существует и установлены все зависимости")
        sys.exit(1)

    try:
        # Вызов реальной функции генерации
        result = generate(
            latitude=lat,
            longitude=lon,
            observation_time=time,
            output_file=output,
            show_planets=show_planets,
            show_grid=show_grid,
            magnitude_limit=magnitude
        )

        click.echo(f"✅ Карта успешно создана: {output}")
        if ctx.obj.get('verbose'):
            click.echo(f"📊 Статистика: {result.get('stars_count', 0)} звезд, "
                       f"{result.get('planets_count', 0)} планет")

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


# ==================== КОМАНДА VERSION ====================

@cli.command()
def version():
    """📌 Показать версию проекта"""
    info_data = get_project_info()

    if "error" not in info_data:
        click.echo(f"{info_data['name']} v{info_data['version']}")
    else:
        click.echo("Версия неизвестна (не удалось прочитать pyproject.toml)")


# ==================== ТОЧКА ВХОДА ====================

if __name__ == '__main__':
    cli()