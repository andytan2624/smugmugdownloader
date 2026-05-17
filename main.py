#!/usr/bin/env python3
"""SmugMug album downloader — copies photos with title, description, and keywords embedded."""

import argparse
import sys
from pathlib import Path


def cmd_auth(_args):
    from auth import run_oauth_flow
    run_oauth_flow()


def cmd_download(args):
    from auth import get_session
    from downloader import download_album
    session = get_session()
    download_album(session, args.album_url, Path(args.output))


def main():
    parser = argparse.ArgumentParser(
        description='Download a SmugMug album with embedded photo metadata.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py auth
  python main.py download https://yourname.smugmug.com/Your-Album
  python main.py download https://yourname.smugmug.com/Your-Album --output ~/Pictures
        """,
    )
    sub = parser.add_subparsers(dest='command', metavar='<command>')

    sub.add_parser('auth', help='Authorize with SmugMug (run once)')

    dl = sub.add_parser('download', help='Download all photos from an album')
    dl.add_argument('album_url', metavar='ALBUM_URL', help='Full SmugMug album URL')
    dl.add_argument(
        '--output', '-o',
        default='./downloads',
        help='Destination folder (default: ./downloads)',
    )

    args = parser.parse_args()

    if args.command == 'auth':
        cmd_auth(args)
    elif args.command == 'download':
        cmd_download(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
