"""Verified downloads and a rollback-safe Windows in-place updater."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import uuid
import zipfile
from .sync import tls_context

REPO = 'https://github.com/JohnLegendstyle/SoulLink'
API = 'https://api.github.com/repos/JohnLegendstyle/SoulLink/releases/latest'
LIMIT = 1024 * 1024 * 1024

def version_tuple(value):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Keine stabile Versionsnummer.')
    return tuple(int(x) for x in value.removeprefix('v').split('.'))

def platform_label(system=None, machine=None):
    system, machine = system or platform.system(), (machine or platform.machine()).lower()
    if system == 'Windows' and machine in ('amd64','x86_64'): return 'Windows-x64'
    if system == 'Darwin' and machine in ('arm64','aarch64'): return 'macOS-arm64'
    raise ValueError('Automatische Updates unterstützen Windows x64 und Macs mit Apple Silicon.')

def release_info(data, current, label):
    if data.get('draft') or data.get('prerelease'): raise ValueError('Kein stabiler Release.')
    tag = data['tag_name']
    if version_tuple(tag) <= version_tuple(current): return None
    version = tag.removeprefix('v')
    name = f'SoulLink-{version}-{label}.zip'
    assets = [a for a in data.get('assets',[]) if a.get('name') == name]
    if len(assets) != 1: raise ValueError('Für dieses System fehlt ein eindeutiges Update-Paket.')
    asset = assets[0]
    url = f'{REPO}/releases/download/{tag}/{name}'
    digest = asset.get('digest','')
    if asset.get('browser_download_url') != url or not re.fullmatch(r'sha256:[a-f0-9]{64}',digest):
        raise ValueError('Downloadadresse oder Prüfsumme ungültig.')
    size = asset.get('size',0)
    if not isinstance(size,int) or not 0 < size <= LIMIT: raise ValueError('Update-Paket ist zu groß oder leer.')
    return dict(version=version,url=url,sha256=digest[7:],size=size,label=label,
                notes=str(data.get('body',''))[:24000],page=f'{REPO}/releases/tag/{tag}')

def check(current):
    request = urllib.request.Request(API,headers={'Accept':'application/vnd.github+json','User-Agent':'SoulLink-Updater'})
    with urllib.request.urlopen(request,timeout=20,context=tls_context()) as response:
        raw = response.read(1024*1024+1)
    if len(raw)>1024*1024: raise ValueError('Release-Antwort zu groß.')
    return release_info(json.loads(raw),current,platform_label())

def extract(archive: Path, destination: Path, label: str):
    """Reject traversal, special files and symlink escapes before writing anything."""
    prefix = 'SoulLink-'+label
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        entries=[]; names=set(); links=set(); total=0
        for item in zipped.infolist():
            if item.filename.startswith('__MACOSX/'): continue
            path=PurePosixPath(item.filename)
            if (not path.parts or path.parts[0]!=prefix or path.is_absolute()
                or any(p in ('..','.') or ':' in p for p in path.parts) or '\\' in item.filename):
                raise ValueError('Unsicherer Pfad im Update.')
            key=str(path).casefold()
            if key in names: raise ValueError('Doppelter Pfad im Update.')
            names.add(key); total+=item.file_size
            if total>4*LIMIT or len(names)>100000: raise ValueError('Entpacktes Update zu groß.')
            mode=item.external_attr>>16
            kind=stat.S_IFMT(mode)
            if kind not in (0,stat.S_IFREG,stat.S_IFDIR,stat.S_IFLNK): raise ValueError('Unzulässiger Dateityp.')
            target=destination.joinpath(*path.parts)
            link=None
            if stat.S_ISLNK(mode):
                if label=='Windows-x64' or item.file_size>4096: raise ValueError('Unzulässige Verknüpfung.')
                link=zipped.read(item).decode('utf-8')
                resolved=(target.parent/link).resolve()
                if Path(link).is_absolute() or not resolved.is_relative_to(destination/prefix):
                    raise ValueError('Verknüpfung verlässt das App-Verzeichnis.')
                links.add(key)
            entries.append((item,path,target,mode,link))
        for _,path,_,_,_ in entries:
            if any(str(p).casefold() in links for p in path.parents):
                raise ValueError('Datei unter einer Verknüpfung.')
        for item,path,target,mode,link in entries:
            target.parent.mkdir(parents=True,exist_ok=True)
            if link is not None: target.symlink_to(link)
            elif item.is_dir(): target.mkdir(exist_ok=True)
            else:
                with zipped.open(item) as src,target.open('xb') as dst: shutil.copyfileobj(src,dst)
                if os.name!='nt': target.chmod((mode & 0o777) or 0o644)
    app=destination/prefix/('SoulLink.exe' if label=='Windows-x64' else 'SoulLink.app')
    executable=app if label=='Windows-x64' else app/'Contents/MacOS/SoulLink'
    if not executable.is_file() or executable.is_symlink(): raise ValueError('App fehlt im Update.')
    return app

def prepare(info, root: Path, progress=lambda value:None):
    root.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=f"{info['version']}-",dir=root))
    archive=stage/'download.zip'
    try:
        digest=hashlib.sha256(); received=0
        request=urllib.request.Request(info['url'],headers={'User-Agent':'SoulLink-Updater'})
        with urllib.request.urlopen(request,timeout=45,context=tls_context()) as response,archive.open('xb') as output:
            if not response.url.startswith('https://'): raise ValueError('Unsichere Download-Verbindung.')
            while chunk:=response.read(1024*1024):
                received+=len(chunk)
                if received>info['size']: raise ValueError('Falsche Downloadgröße.')
                output.write(chunk);digest.update(chunk);progress(int(received*100/info['size']))
        if received!=info['size'] or digest.hexdigest()!=info['sha256']:
            raise ValueError('Update-Prüfsumme stimmt nicht. Nichts installiert.')
        app=extract(archive,stage,info['label'])
        archive.unlink()
        return app
    except Exception:
        # Only the private staging directory created by this invocation is removed.
        shutil.rmtree(stage)
        raise


WINDOWS_UPDATE_SCRIPT = r'''param(
    [Parameter(Mandatory=$true)][int]$ParentPid,
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string]$Backup,
    [Parameter(Mandatory=$true)][string]$Log
)
$ErrorActionPreference = 'Stop'
try {
    Wait-Process -Id $ParentPid -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    New-Item -ItemType Directory -Path $Backup -Force | Out-Null
    $installed = New-Object System.Collections.Generic.List[string]
    foreach ($item in Get-ChildItem -LiteralPath $Source -Force) {
        $name = $item.Name
        $target = Join-Path $Destination $name
        $old = Join-Path $Backup $name
        if (Test-Path -LiteralPath $target) {
            Move-Item -LiteralPath $target -Destination $old -Force
        }
        Move-Item -LiteralPath $item.FullName -Destination $target -Force
        $installed.Add($name)
    }
    "Update erfolgreich: $(Get-Date -Format o)" | Set-Content -LiteralPath $Log -Encoding UTF8
    Start-Process -FilePath (Join-Path $Destination 'SoulLink.exe') -WorkingDirectory $Destination
} catch {
    "Update fehlgeschlagen: $($_.Exception.Message)" | Set-Content -LiteralPath $Log -Encoding UTF8
    foreach ($name in $installed) {
        $target = Join-Path $Destination $name
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
    }
    if (Test-Path -LiteralPath $Backup) {
        foreach ($item in Get-ChildItem -LiteralPath $Backup -Force) {
            Move-Item -LiteralPath $item.FullName -Destination (Join-Path $Destination $item.Name) -Force
        }
    }
    exit 1
}
'''


def schedule_windows_update(app: Path, destination: Path, updates_root: Path, parent_pid: int | None = None):
    """Start an external process that swaps the verified package after exit."""
    if platform.system() != 'Windows':
        raise ValueError('Das direkte Ersetzen ist in dieser Version nur unter Windows verfügbar.')
    app = app.resolve()
    source = app.parent
    destination = destination.resolve()
    updates_root = updates_root.resolve()
    if app.name.casefold() != 'soullink.exe' or source.name != 'SoulLink-Windows-x64':
        raise ValueError('Das geprüfte Windows-Updatepaket ist unvollständig.')
    if not app.is_file() or not source.is_relative_to(updates_root):
        raise ValueError('Ungültiger Update-Pfad.')
    if destination == source or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('Updatequelle und installierte App dürfen sich nicht überlappen.')
    if not (destination / 'SoulLink.exe').is_file():
        raise ValueError('Der bisherige Soul-Link-Installationsordner wurde nicht erkannt.')

    job = updates_root / ('apply-' + uuid.uuid4().hex)
    backup = job / 'rollback'
    log = job / 'update.log'
    job.mkdir(parents=True, exist_ok=False)
    script = job / 'apply-update.ps1'
    script.write_text(WINDOWS_UPDATE_SCRIPT, encoding='utf-8')
    command = [
        'powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', str(script), '-ParentPid', str(parent_pid or os.getpid()),
        '-Source', str(source), '-Destination', str(destination),
        '-Backup', str(backup), '-Log', str(log),
    ]
    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    return subprocess.Popen(command, cwd=str(job), creationflags=creationflags)
