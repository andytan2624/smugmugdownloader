from urllib.parse import urlparse

BASE_URL = 'https://api.smugmug.com/api/v2'


def _get(session, path, params=None):
    url = path if path.startswith('http') else f"{BASE_URL}{path}"
    resp = session.get(url, params=params or {}, headers={'Accept': 'application/json'})
    resp.raise_for_status()
    return resp.json()['Response']


def _parse_smugmug_url(album_url):
    """Return (username, url_path) from a SmugMug album URL."""
    parsed = urlparse(album_url)
    host = parsed.netloc
    if host.endswith('.smugmug.com') and not host.startswith('www.'):
        username = host[: -len('.smugmug.com')]
        url_path = parsed.path.strip('/')
    else:
        parts = parsed.path.strip('/').split('/', 1)
        username = parts[0]
        url_path = parts[1] if len(parts) > 1 else ''
    return username, url_path


def lookup_album(session, album_url):
    # Try the fast endpoint first; fall back to scanning the user's album list.
    try:
        data  = _get(session, '!lookupUrl', {'url': album_url})
        album = data.get('Album')
        if album:
            return album
    except Exception:
        pass

    username, url_path = _parse_smugmug_url(album_url)
    start, count = 1, 100
    while True:
        data   = _get(session, f'/user/{username}!albums', {'start': start, 'count': count})
        albums = data.get('Album', [])
        for album in albums:
            if album.get('UrlPath', '').strip('/') == url_path:
                return album
        pages = data.get('Pages', {})
        if start + len(albums) - 1 >= pages.get('Total', len(albums)):
            break
        start += count

    raise ValueError(f"No album found at URL: {album_url}")


def get_album_images(session, album_key):
    images, start, count = [], 1, 100
    while True:
        data  = _get(session, f'/album/{album_key}!images', {'start': start, 'count': count})
        batch = data.get('AlbumImage', [])
        images.extend(batch)
        total = data.get('Pages', {}).get('Total', len(images))
        if len(images) >= total:
            break
        start += count
    return images


def get_download_url(session, image_key):
    data = _get(session, f'/image/{image_key}!download')
    return data.get('ImageDownload', {}).get('Url')
