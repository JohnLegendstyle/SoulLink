from soullink.app import main
import sys

def self_test():
    import tkinter as tk
    import subprocess
    import platform
    from soullink.randomizer import runtime_root, install_root, java_binary, classpath
    from soullink.save_reader import read_save
    from soullink.melonds import find_executable
    gui=tk.Tk();gui.withdraw();gui.update();gui.destroy()
    for name in ('Optimus','Bee'):
        state=read_save(runtime_root()/'checkpoints'/f'{name}.sav')
        assert state.trainer==name and state.gender==0 and not state.party
    subprocess.run([java_binary(),'-version'],check=True,capture_output=True)
    classpath()
    emulator=install_root()/'Emulator'/('melonDS.app' if platform.system()=='Darwin' else 'melonDS.exe')
    find_executable(emulator)

if __name__ == "__main__":
    if '--self-test' in sys.argv:
        try: self_test()
        except Exception:
            import traceback
            from pathlib import Path
            Path('soullink-self-test-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
            sys.exit(1)
    else: main()
