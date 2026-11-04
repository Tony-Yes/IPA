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


def build_entry(config):
    repo = config['repo']
    release = json.loads(fetch(f'https://api.github.com/repos/{repo}/releases/latest'))
    candidates = [a for a in release['assets'] if re.fullmatch(config['asset_pattern'], a['name'])]
    if len(candidates) != 1:
        raise RuntimeError(f'Expected exactly one unsigned IPA, got {len(candidates)}')
    asset = candidates[0]
    data = fetch(asset['browser_download_url'])
    if len(data) != asset['size']:
        raise RuntimeError('IPA size mismatch')
    checksum_asset = next((a for a in release['assets'] if a['name'] == 'SHA256SUMS'), None)
    digest = hashlib.sha256(data).hexdigest()
    verified = False
    if config.get('require_sha256sums'):
        if checksum_asset is None:
            raise RuntimeError('Release has no SHA256SUMS')
        expected = None
        for line in fetch(checksum_asset['browser_download_url']).decode().splitlines():
            fields = line.split(maxsplit=1)
            if len(fields) == 2 and fields[1].lstrip('*') == asset['name']:
                expected = fields[0].lower()
        if expected != digest:
            raise RuntimeError('SHA256 verification failed')
        verified = True
    elif asset.get('digest'):
        if asset['digest'] != 'sha256:' + digest:
            raise RuntimeError('GitHub asset digest mismatch')
        verified = True
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        paths = [n for n in archive.namelist() if re.fullmatch(r'Payload/[^/]+\.app/Info\.plist', n)]
        if len(paths) != 1:
            raise RuntimeError('Expected one main app Info.plist')
        info = plistlib.loads(archive.read(paths[0]))
    version = str(info['CFBundleShortVersionString'])
    date = release['published_at']
    icon = config['icon_url']
    entry = {
        'name': config['name'],
        'bundleIdentifier': info['CFBundleIdentifier'],
        'developerName': repo.split('/')[0],
        'localizedDescription': config.get('description', 'Official GitHub release. Sign before installation.'),
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
    print(json.dumps({'name': config['name'], 'tag': release['tag_name'],
                      'version': version, 'bundleIdentifier': info['CFBundleIdentifier'],
                      'size': len(data), 'sha256': digest, 'checksumVerified': verified}))
    return entry


def main():
    configs = json.loads((ROOT / 'apps.json').read_text())
    previous_path = ROOT / 'source.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {'apps': []}
    old = {app['name']: app for app in previous['apps']}
    entries = []
    failures = []
    for config in configs:
        try:
            entries.append(build_entry(config))
        except Exception as exc:
            failures.append(config['name'])
            print(f"::warning::{config['name']}: {exc}")
            if config['name'] not in old:
                raise RuntimeError(f"No previous entry for {config['name']}; source left unchanged") from exc
            entries.append(old[config['name']])
    if len(failures) == len(configs):
        raise RuntimeError('All app updates failed; source left unchanged')
    source = {
        'name': 'MoviePilot + qBitController',
        'identifier': 'community.moviepilot.github.source',
        'subtitle': 'Unofficial feed for official GitHub releases',
        'apps': entries, 'news': []
    }
    target = ROOT / 'source.json'
    tmp = ROOT / 'source.json.tmp'
    tmp.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(target)


if __name__ == '__main__':
    main()
