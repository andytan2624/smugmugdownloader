import subprocess
import sys
from pathlib import Path

from smugmug_api import lookup_album, get_album_images, get_download_url


def _check_exiftool():
    if subprocess.run(['which', 'exiftool'], capture_output=True).returncode != 0:
        print("Error: exiftool is not installed.")
        print("Install it with:  brew install exiftool")
        sys.exit(1)


def _write_metadata(filepath, title, description, keywords):
    cmd = ['exiftool', '-overwrite_original', '-q']

    if title:
        cmd += [
            f'-Title={title}',
            f'-XPTitle={title}',
            f'-ObjectName={title}',       # IPTC
        ]
    if description:
        cmd += [
            f'-Description={description}',
            f'-ImageDescription={description}',   # EXIF
            f'-Caption-Abstract={description}',   # IPTC
        ]
    if keywords:
        for kw in (k.strip() for k in keywords.split(',') if k.strip()):
            cmd += [f'-Keywords+={kw}', f'-Subject+={kw}']

    cmd.append(str(filepath))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [warn] exiftool: {result.stderr.strip()}")


def _download_file(session, url, dest):
    resp = session.get(url, stream=True)
    resp.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)


def download_album(session, album_url, output_dir: Path):
    _check_exiftool()

    print(f"Looking up album: {album_url}")
    album     = lookup_album(session, album_url)
    album_key = album['AlbumKey']
    album_name = album.get('Name', album_key)
    print(f"Album: {album_name}")

    safe_name = "".join(c if c.isalnum() or c in ' -_.' else '_' for c in album_name).strip()
    dest_dir  = output_dir / safe_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching image list...")
    images = get_album_images(session, album_key)
    total  = len(images)
    print(f"Found {total} image(s)\n")

    errors = []
    for i, img in enumerate(images, 1):
        image_key   = img.get('ImageKey', '')
        filename    = img.get('FileName') or f'image_{i:04d}.jpg'
        title       = img.get('Title', '')
        description = img.get('Caption', '')
        keywords    = img.get('Keywords', '')
        dest_path   = dest_dir / filename

        prefix = f"[{i}/{total}] {filename}"

        if dest_path.exists():
            print(f"{prefix} — skipped (already exists)")
            continue

        # Prefer ArchivedUri (original quality); fall back to !download endpoint
        url = img.get('ArchivedUri') or get_download_url(session, image_key)
        if not url:
            print(f"{prefix} — ERROR: no download URL")
            errors.append(filename)
            continue

        try:
            print(f"{prefix} — downloading...", end='', flush=True)
            _download_file(session, url, dest_path)

            if title or description or keywords:
                _write_metadata(dest_path, title, description, keywords)
                print(" saved + metadata written")
            else:
                print(" saved (no metadata)")

        except Exception as exc:
            print(f" ERROR: {exc}")
            errors.append(filename)
            dest_path.unlink(missing_ok=True)

    print(f"\nDone. Photos saved to: {dest_dir.resolve()}")
    if errors:
        print(f"Failed ({len(errors)}): {', '.join(errors)}")
