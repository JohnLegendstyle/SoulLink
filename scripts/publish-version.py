"""Freeze a verified rolling build as a numbered GitHub release; never replace assets.

Usage: python scripts/publish-version.py VERSION BUILD_RUN_ID
Requires the repository's existing Git credential (contents write, not workflow write).
The rolling build must still match this run. Credentials are never printed or stored.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
import zipfile

repo = 'JohnLegendstyle/SoulLink'
version, run_id = sys.argv[1:]
if not all(p.isdigit() for p in version.split('.')) or len(version.split('.')) != 3 or not run_id.isdigit():
    raise SystemExit('Expected numeric VERSION and BUILD_RUN_ID')
root = Path(__file__).resolve().parent.parent
notes = (root / 'releases' / f'v{version}.md').read_text()
credential = subprocess.run(['git','credential','fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, check=True)
fields = dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
token = fields['password']

def api(path, data=None, method=None, binary=False):
    url = path if path.startswith('https://uploads.github.com/') else f'https://api.github.com/repos/{repo}/{path}'
    body = data if binary else (json.dumps(data).encode() if data is not None else None)
    request = urllib.request.Request(url, data=body, method=method, headers={
        'Authorization':'Bearer '+token, 'Accept':'application/vnd.github+json',
        'Content-Type':'application/octet-stream' if binary else 'application/json',
        'User-Agent':'SoulLink-version-publisher'})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)

run = api(f'actions/runs/{run_id}')
assert run['conclusion'] == 'success' and run['name'] == 'Desktop Apps', 'Build must be successful'
sha = run['head_sha']
source = subprocess.check_output(['git','show',f'{sha}:desktop/soullink/__init__.py'],text=True)
assert f'"{version}"' in source or f"'{version}'" in source, 'Source version mismatch'
rolling = api('releases/tags/spielabend')
expected = {'SoulLink-Windows-x64.zip','SoulLink-macOS-arm64.zip','SoulLink-Startspielstaende.zip'}
assets = [a for a in rolling['assets'] if a['name'] in expected]
assert {a['name'] for a in assets} == expected
assert all(run['created_at'] <= a['updated_at'] <= run['updated_at'] for a in assets), 'Rolling assets no longer match this build'
try:
    existing = api(f'releases/tags/v{version}')
except urllib.error.HTTPError as error:
    if error.code != 404: raise
    existing = None
if existing and not existing['draft']:
    raise SystemExit('Version is already published; refusing to replace it')

with tempfile.TemporaryDirectory(prefix='soullink-release-') as temp:
    ready = []
    for asset in assets:
        name = asset['name'].replace('SoulLink-',f'SoulLink-{version}-',1)
        path = Path(temp) / name
        # Public download: no credential forwarded to asset/CDN redirects.
        with urllib.request.urlopen(asset['browser_download_url'], timeout=180) as response, path.open('wb') as output:
            while block := response.read(1024*1024): output.write(block)
        assert path.stat().st_size == asset['size'], 'Size mismatch'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert asset.get('digest') == 'sha256:'+digest, 'GitHub asset checksum mismatch'
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None, 'Broken archive'
            assert any(n.endswith('SPIELSTART.md') for n in archive.namelist())
        ready.append((name,path,digest))
    release = existing or api('releases', {'tag_name':f'v{version}','target_commitish':sha,
        'name':notes.splitlines()[0].lstrip('# ').strip(),
        'body':notes,'draft':True,'prerelease':False})
    upload = release['upload_url'].split('{')[0]
    present = {a['name']:a for a in release['assets']}
    sums = ''.join(f'{digest}  {name}\n' for name,path,digest in ready).encode()
    uploads = [(name,path.read_bytes()) for name,path,digest in ready]+[('SHA256SUMS.txt',sums)]
    for name, content in uploads:
        if name in present:
            assert present[name].get('digest') == 'sha256:'+hashlib.sha256(content).hexdigest()
            continue
        api(upload+'?name='+name,content,binary=True)
    api(f"releases/{release['id']}",{'draft':False,'make_latest':'true','body':notes},method='PATCH')
    print(f'Published v{version}: {len(uploads)} checked assets; source {sha}')

# Historical packages remain byte-for-byte untouched; label the archive clearly.
for old in api('releases?per_page=100'):
    tag = old['tag_name']
    if tag in ('v0.2.0','v0.3.0','v0.4.0'):
        intro = f'Archivierte Version {tag[1:]}. Für den aktuellen Spielbetrieb bitte [die stabile Version](https://github.com/{repo}/releases/latest) verwenden. Diese alten Pakete werden unverändert aufbewahrt.\n\n'
        body = old['body'] or ''
        if not body.startswith(intro): body = intro + body
        api(f"releases/{old['id']}",{'name':f'Soul Link {tag[1:]} – Archiv','body':body,'make_latest':'false'},method='PATCH')
    elif tag == 'spielabend':
        api(f"releases/{old['id']}",{'name':'Soul Link – fortlaufender Build (kein Versionsarchiv)',
            'body':f'Dieser technische Build-Kanal wird bei neuen Desktop-Builds ersetzt. Für klar versionierte Downloads, Update-Hinweise und Änderungsübersichten bitte [die aktuelle stabile Version](https://github.com/{repo}/releases/latest) oder [das Versionsarchiv](https://github.com/{repo}/blob/main/CHANGELOG.md) verwenden. Keine Startspielstände über bestehenden Fortschritt kopieren.',
            'prerelease':True,'make_latest':'false'},method='PATCH')
