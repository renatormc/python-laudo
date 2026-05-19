from pathlib import Path

from .exif import get_caption


def collect_assets(assets_path: Path) -> dict[str, dict]:
    assets: dict[str, dict] = {}
    if not assets_path.is_dir():
        return assets
    for f in sorted(assets_path.iterdir()):
        if f.is_file():
            caption = get_caption(f) if f.suffix.lower() in {".jpg", ".jpeg", ".tiff", ".png"} else ""
            assets[f.stem] = {"path": f, "caption": caption}
    return assets
