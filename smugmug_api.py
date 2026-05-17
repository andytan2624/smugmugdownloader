BASE_URL = 'https://api.smugmug.com/api/v2'


def _get(session, path, params=None):
    url = path if path.startswith('http') else f"{BASE_URL}{path}"
    resp = session.get(url, params=params or {}, headers={'Accept': 'application/json'})
    resp.raise_for_status()
    return resp.json()['Response']


def lookup_album(session, album_url):
    data  = _get(session, '!lookupUrl', {'url': album_url})
    album = data.get('Album')
    if not album:
        raise ValueError(f"No album found at URL: {album_url}")
    return album


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
