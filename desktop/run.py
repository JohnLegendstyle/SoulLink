from soullink.app import main
import sys

def self_test():
    import tkinter as tk
    import subprocess
    import platform
    from soullink.randomizer import runtime_root, install_root, java_binary, classpath
    from soullink.save_reader import read_save
    from soullink.melonds import find_executable
    from soullink.skins import load_skin
    from soullink.jedi import roster, load_character
    import ndspy.texture
    gui=tk.Tk();gui.withdraw();gui.update();gui.destroy()
    for name in ('Optimus','Bee'):
        load_skin(name)
        state=read_save(runtime_root()/'checkpoints'/f'{name}.sav')
        assert state.trainer==name and state.gender==0 and not state.party
    for character in roster():load_character(character['id'])
    subprocess.run([java_binary(),'-version'],check=True,capture_output=True)
    classpath()
    emulator=install_root()/'Emulator'/('melonDS.app' if platform.system()=='Darwin' else 'melonDS.exe')
    executable=find_executable(emulator)
    assert (install_root()/'Emulator'/'focus-version.txt').read_text().strip()=='focus-0.12.1'
    native=subprocess.run([str(executable),'--help'],capture_output=True,text=True,timeout=20)
    if native.returncode:
        raise RuntimeError(f'Emulator self-test failed ({native.returncode}): {native.stdout}\n{native.stderr}')
    from soullink.sync import tls_context
    context=tls_context()
    assert context.cert_store_stats()['x509_ca'] > 0
    if '--network-check' in sys.argv:
        import urllib.request, json
        with urllib.request.urlopen('https://soullink-web-production.up.railway.app/health',context=context,timeout=15) as response:
            assert json.load(response)['ok']

if __name__ == "__main__":
    if '--self-test' in sys.argv:
        try: self_test()
        except Exception:
            import traceback
            from pathlib import Path
            Path('soullink-self-test-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
            sys.exit(1)
    else: main()
