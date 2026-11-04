import hashlib
import io
import json
import os
import plistlib
import re
import urllib.request
import zipfile
from pathlib import Path

REPO = 'jxxghp/MoviePilot-App'
ROOT = Path(__file__).resolve().parent

def fetch(url):
    headers = {'User-Agent': 'MoviePilot-source-updater'}
    if url.startswith('https://api.github.com/') and os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def main():
    release = json.loads(fetch(f'https://api.github.com/repos/{REPO}/releases/latest'))
    candidates = [a for a in release['assets'] if re.fullmatch(r'MoviePilot-.+-unsigned\.ipa', a['name'])]
    if len(candidates) != 1:
        raise RuntimeError(f'Expected exactly one unsigned IPA, got {len(candidates)}')
    asset = candidates[0]
    data = fetch(asset['browser_download_url'])
    if len(data) != asset['size']:
        raise RuntimeError('IPA size mismatch')
    checksum_asset = next((a for a in release['assets'] if a['name'] == 'SHA256SUMS'), None)
    if checksum_asset is None:
        raise RuntimeError('Release has no SHA256SUMS')
    expected = None
    for line in fetch(checksum_asset['browser_download_url']).decode().splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) == 2 and fields[1].lstrip('*') == asset['name']:
            expected = fields[0].lower()
    digest = hashlib.sha256(data).hexdigest()
    if expected != digest:
        raise RuntimeError('SHA256 verification failed')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        paths = [n for n in archive.namelist() if re.fullmatch(r'Payload/[^/]+\.app/Info\.plist', n)]
        if len(paths) != 1:
            raise RuntimeError('Expected one main app Info.plist')
        info = plistlib.loads(archive.read(paths[0]))
    version = str(info['CFBundleShortVersionString'])
    date = release['published_at']
    icon = f'https://raw.githubusercontent.com/{REPO}/main/ios/MoviePilot/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png'
    entry = {
        'name': 'MoviePilot',
        'bundleIdentifier': info['CFBundleIdentifier'],
        'developerName': 'jxxghp',
        'localizedDescription': 'MoviePilot iOS client. Unsigned official GitHub release; sign before installation.',
        'iconURL': icon,
        'version': version,
        'versionDate': date,
        'downloadURL': asset['browser_download_url'],
        'size': len(data),
        'versions': [{
            'version': version, 'date': date,
            'downloadURL': asset['browser_download_url'], 'size': len(data),
            **({'minOSVersion': info['MinimumOSVersion']} if info.get('MinimumOSVersion') else {})
        }]
    }
    source = {
        'name': 'MoviePilot GitHub Source',
        'identifier': 'community.moviepilot.github.source',
        'subtitle': 'Unofficial feed for official unsigned releases',
        'apps': [entry], 'news': []
    }
    target = ROOT / 'source.json'
    tmp = ROOT / 'source.json.tmp'
    tmp.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(target)
    print(json.dumps({'tag': release['tag_name'], 'version': version,
                      'bundleIdentifier': info['CFBundleIdentifier'],
                      'size': len(data), 'sha256': digest}, ensure_ascii=False))

if __name__ == '__main__':
    main()
