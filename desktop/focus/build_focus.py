"""Build the Focus Qt frontend on macOS/Windows, preserving melonDS core.

Dependency installation is restricted to disposable CI runners. Local builds
use already installed dependencies and never install a system package manager.
"""
from pathlib import Path
import hashlib
import os
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile
from .apply_focus import apply

VERSION='focus-0.15.4'


def run(args, **kwargs):
    print('+', ' '.join(map(str,args)),flush=True)
    return subprocess.run(list(map(str,args)),check=True,**kwargs)


def build(root: Path):
    vendor=root/'vendor'
    output=vendor/'FocusEmulator'
    marker=output/'focus-version.txt'
    if marker.is_file() and marker.read_text().strip()==VERSION: return output
    source_dir=vendor/'focus-build-source'
    if source_dir.exists():
        raise RuntimeError('Focus source build folder already exists; use a fresh build directory.')
    source_dir.mkdir()
    with zipfile.ZipFile(vendor/'Quelltexte'/'melonDS-1.1.zip') as archive:
        archive.extractall(source_dir)
    source=source_dir/'melonDS-1.1'
    apply(source)
    shutil.copy2(Path(__file__).with_name('test_layout.cpp'),source/'focus-layout-test.cpp')
    with (source/'CMakeLists.txt').open('a') as cmake:
        cmake.write('\nadd_executable(focus-layout-test focus-layout-test.cpp src/frontend/ScreenLayout.cpp)\n'
                    'target_include_directories(focus-layout-test PRIVATE src/frontend)\n'
                    'target_compile_options(focus-layout-test PRIVATE -UNDEBUG)\n')
    # Ship the complete modified source alongside the original pinned source.
    shutil.make_archive(str(vendor/'Quelltexte'/'SoulLink-Focus-source'),'zip',source_dir,'melonDS-1.1')
    build_dir=vendor/'focus-build'
    output.mkdir(exist_ok=True)
    env=os.environ.copy()
    if platform.system()=='Darwin':
        deps=['qtbase','qtmultimedia','qtsvg','sdl2','libarchive','enet','zstd','faad2','pkg-config','cmake','ninja']
        if env.get('GITHUB_ACTIONS')=='true':
            env['HOMEBREW_NO_AUTO_UPDATE']='1'
            run(['brew','install',*deps],env=env)
            modern_xcode=Path('/Applications/Xcode_16.2.app/Contents/Developer')
            if modern_xcode.exists(): env['DEVELOPER_DIR']=str(modern_xcode)
        prefixes=[subprocess.check_output(['brew','--prefix',p],text=True).strip() for p in deps[:8]]
        prefixes.insert(0,subprocess.check_output(['brew','--prefix'],text=True).strip())
        env['PKG_CONFIG_PATH']=':'.join(str(Path(p)/'lib/pkgconfig') for p in prefixes)
        env['SOULLINK_FRAMEWORK_PATHS']=':'.join(str(Path(p)/'lib') for p in prefixes)
        run(['cmake','-S',source,'-B',build_dir,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_PREFIX_PATH='+';'.join(prefixes),'-DQT_ADDITIONAL_PACKAGES_PREFIX_PATH='+';'.join(prefixes),
             '-DENABLE_LTO_RELEASE=OFF','-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0'],env=env)
        run(['cmake','--build',build_dir,'--parallel','3'],env=env)
        run([build_dir/'focus-layout-test'],env=env)
        # Homebrew now supplies sdl2-compat, which dlopens SDL3. It does not
        # appear in otool's dependency list; bundle it next to the SDL2 library.
        sdl3=Path(prefixes[0])/'lib/libSDL3.dylib'
        if sdl3.exists():
            frameworks=build_dir/'melonDS.app/Contents/Frameworks'
            frameworks.mkdir(exist_ok=True)
            shutil.copy2(sdl3.resolve(),frameworks/'libSDL3.dylib')
            env['SOULLINK_SDL3_SOURCE']=str(sdl3.resolve())
        # Upstream bundler is compatible with system Ruby 2.6 (File.exists?).
        run(['/usr/bin/ruby',source/'tools/mac-libs.rb',build_dir],env=env)
        shutil.copytree(build_dir/'melonDS.app',output/'melonDS.app',symlinks=True)
    elif platform.system()=='Windows':
        msys=Path(os.environ.get('SOULLINK_MSYS2','C:/msys64'))
        if not (msys/'usr/bin/bash.exe').exists():
            if env.get('GITHUB_ACTIONS')!='true': raise RuntimeError('Install MSYS2 UCRT64 build dependencies first.')
            package=vendor/'msys2-base.tar.xz'
            urllib.request.urlretrieve('https://github.com/msys2/msys2-installer/releases/download/2026-06-11/msys2-base-x86_64-20260611.tar.xz',package)
            if hashlib.sha256(package.read_bytes()).hexdigest()!='a2d047e8ee213c3c6a49a8de427eb1069df12207c0422ff1b3cbb5c905c34221':
                raise ValueError('MSYS2 checksum mismatch')
            with tarfile.open(package) as archive: archive.extractall(vendor/'tools',filter='data')
            msys=vendor/'tools/msys64'
        shell=msys/'usr/bin/bash.exe'
        env.update({'MSYSTEM':'UCRT64','CHERE_INVOKING':'1','MSYS2_PATH_TYPE':'inherit'})
        if env.get('GITHUB_ACTIONS')=='true':
            run([shell,'-lc','true'],env=env)
            packages=['gcc','cmake','ninja','pkgconf','SDL2','libarchive','enet','zstd','faad2','qt6-base','qt6-multimedia','qt6-svg','qt6-tools']
            run([shell,'-lc','pacman -Sy --noconfirm --needed '+ ' '.join('mingw-w64-ucrt-x86_64-'+p for p in packages)],env=env)
        prefix=msys/'ucrt64'
        env['PATH']=str(prefix/'bin')+os.pathsep+str(msys/'usr/bin')+os.pathsep+env['PATH']
        env['PKG_CONFIG_PATH']=str(prefix/'lib/pkgconfig')
        cmake=prefix/'bin/cmake.exe'
        run([cmake,'-S',source,'-B',build_dir,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_C_COMPILER='+str(prefix/'bin/gcc.exe'),'-DCMAKE_CXX_COMPILER='+str(prefix/'bin/g++.exe'),
             '-DCMAKE_PREFIX_PATH='+str(prefix),'-DENABLE_LTO_RELEASE=OFF'],env=env)
        run([cmake,'--build',build_dir,'--parallel','3'],env=env)
        run([build_dir/'focus-layout-test.exe'],env=env)
        shutil.copy2(build_dir/'melonDS.exe',output/'melonDS.exe')
        deploy=next(prefix.rglob('windeployqt.exe'))
        run([deploy,'--release','--no-translations','--no-opengl-sw',output/'melonDS.exe'],env=env)
        # Resolve all non-system dependencies recursively, not only Qt DLLs.
        available={p.name.lower():p for p in (prefix/'bin').glob('*.dll')}
        if 'sdl3.dll' in available: shutil.copy2(available['sdl3.dll'],output/'SDL3.dll')
        pending=list(output.rglob('*.dll'))+[output/'melonDS.exe']; seen=set()
        while pending:
            binary=pending.pop()
            if str(binary) in seen: continue
            seen.add(str(binary))
            info=subprocess.check_output([str(prefix/'bin/objdump.exe'),'-p',str(binary)],env=env,text=True,errors='replace')
            for dependency in re.findall(r'DLL Name:\s*(\S+)',info):
                origin=available.get(dependency.lower())
                if origin:
                    target=output/origin.name
                    if not target.exists(): shutil.copy2(origin,target)
                    pending.append(target)
    else:
        raise RuntimeError('Focus package supports macOS and Windows builds.')
    marker.write_text(VERSION+'\n')
    return output
