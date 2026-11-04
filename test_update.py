import io
import json
import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import update

class FeedTests(unittest.TestCase):
    def test_configured_apps_are_generated_from_real_plist(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('Payload/Test.app/Info.plist', plistlib.dumps({
                'CFBundleIdentifier': 'test.bundle', 'CFBundleShortVersionString': '1.2',
                'MinimumOSVersion': '15.0'}))
        data = buf.getvalue()
        release = {'tag_name': 'v1.2', 'published_at': '2026-01-01T00:00:00Z',
                   'assets': [{'name': 'test-ios.ipa', 'size': len(data),
                               'browser_download_url': 'https://example.com/test.ipa'}]}
        config = [{'name': n, 'repo': 'test/' + n, 'asset_pattern': r'.*-ios\.ipa',
                   'icon_url': 'https://example.com/icon.png'} for n in ['One', 'Two']]
        def fetch(url):
            return json.dumps(release).encode() if 'api.github.com' in url else data
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'apps.json').write_text(json.dumps(config))
            with patch.object(update, 'ROOT', root), patch.object(update, 'fetch', fetch):
                update.main()
            apps = json.loads((root / 'source.json').read_text())['apps']
            self.assertEqual([a['name'] for a in apps], ['One', 'Two'])
            self.assertEqual(apps[1]['bundleIdentifier'], 'test.bundle')
            self.assertEqual(apps[1]['versions'][0]['minOSVersion'], '15.0')

    def test_failed_app_preserves_previous_entry(self):
        configs = [{'name': 'One'}, {'name': 'Two'}]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'apps.json').write_text(json.dumps(configs))
            (root / 'source.json').write_text(json.dumps({'apps': [{'name': 'Two', 'version': 'old'}]}))
            def build(config):
                if config['name'] == 'Two':
                    raise RuntimeError('network failure')
                return {'name': 'One', 'version': 'new'}
            with patch.object(update, 'ROOT', root), patch.object(update, 'build_entry', build):
                update.main()
            apps = json.loads((root / 'source.json').read_text())['apps']
            self.assertEqual(apps, [{'name': 'One', 'version': 'new'}, {'name': 'Two', 'version': 'old'}])

if __name__ == '__main__':
    unittest.main()
