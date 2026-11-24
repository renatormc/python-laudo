import shutil
from pathlib import Path

from PIL import Image, ImageOps

from .docxzip import DocxZip

SUPPORTED_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp")
DOC_EXTENSIONS: tuple[str, ...] = (".docx", ".odt")
DEFAULT_FOLDER_MAX = 450
DEFAULT_DOC_MAX = 450
RESOLUTION_CHOICES: tuple[int, ...] = (300, 450, 600, 800, 1024, 1280, 1600, 1920)
DEFAULT_RESOLUTION = 450


def resize_large_image(path: Path, dest: Path, max_resolution: int = DEFAULT_FOLDER_MAX) -> bool:
    """Resize ``path`` into ``dest`` if larger than ``max_resolution``.

    Returns True if the image was resized. Images that are already small are
    copied unchanged (or left untouched when ``dest`` is ``path``).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(path) as original:
        fmt = original.format
        width, height = original.size  # header only: small images are never decoded
        if width <= max_resolution and height <= max_resolution:
            if path.resolve() != dest.resolve():
                shutil.copy2(path, dest)
            print(f"Copied {path.name} (no resizing needed)")
            return False

        original.load()  # releases the file so ``dest`` may overwrite ``path``
        img = ImageOps.exif_transpose(original) or original
        width, height = img.size
        img.thumbnail((max_resolution, max_resolution), Image.Resampling.LANCZOS)
        new_width, new_height = img.size
        if fmt == "JPEG" and img.mode not in ("RGB", "L", "CMYK"):
            img = img.convert("RGB")
        img.save(dest, format=fmt, quality=95, optimize=True)
    print(f"Resized {path.name} from {width}x{height} to {new_width}x{new_height}")
    return True


def resize_large_images(
    source_folder: Path,
    dest_folder: Path,
    max_resolution: int = DEFAULT_FOLDER_MAX,
    overwrite: bool = True,
) -> None:
    """Resize every image in ``source_folder`` (recursively) into ``dest_folder``."""
    from concurrent.futures import ThreadPoolExecutor

    dest_folder.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[Path, Path]] = []
    for source_path in sorted(source_folder.rglob("*")):
        if not source_path.is_file() or source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        dest_path = dest_folder / source_path.relative_to(source_folder)
        if overwrite or not dest_path.exists():
            jobs.append((source_path, dest_path))

    def run(job: tuple[Path, Path]) -> None:
        source_path, dest_path = job
        try:
            resize_large_image(source_path, dest_path, max_resolution=max_resolution)
        except Exception as e:
            print(f"Error processing {source_path.name}: {e}")

    # Pillow releases the GIL while decoding/encoding, so threads give a real speedup.
    with ThreadPoolExecutor() as pool:
        list(pool.map(run, jobs))


def reduce_doc_images(path: Path, dest: Path, max_resolution: int = DEFAULT_DOC_MAX) -> None:
    """Reduce the images embedded in a .docx/.odt file and save it to ``dest``."""
    with DocxZip(path) as doc:
        if doc.image_folder.is_dir():
            resize_large_images(doc.image_folder, doc.image_folder, max_resolution=max_resolution)
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.save(dest)


def reduce_images(source: Path, dest: Path, max_resolution: int | None = None) -> None:
    """Reduce images from a folder into another folder, or inside a document."""
    if source.is_dir():
        if (dest.exists() and not dest.is_dir()) or dest.suffix.lower() in DOC_EXTENSIONS:
            raise ValueError(f"Destination must be a folder: {dest}")
        resize_large_images(source, dest, max_resolution=max_resolution or DEFAULT_FOLDER_MAX)
    elif source.is_file() and source.suffix.lower() in DOC_EXTENSIONS:
        if dest.suffix.lower() != source.suffix.lower():
            raise ValueError(f"Destination must be a {source.suffix} file: {dest}")
        reduce_doc_images(source, dest, max_resolution=max_resolution or DEFAULT_DOC_MAX)
    else:
        raise ValueError(f"Source must be a folder or a .docx/.odt file: {source}")
