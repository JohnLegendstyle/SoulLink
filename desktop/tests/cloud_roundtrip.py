"""Real client/server integration; stdin contains isolated test-room credentials."""
import json
import sys
import tempfile
import time
from pathlib import Path
from soullink.cloud import CloudSession, CloudError, CloudConflict

access=json.load(sys.stdin)
original=(Path(__file__).parents[1]/'randomizer/checkpoints/Optimus.sav').read_bytes()
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    def device(name):
        folder=root/name;folder.mkdir()
        save=folder/'Optimus.sav';save.write_bytes(original)
        rom=folder/'game.nds';rom.write_bytes(b'integration-identical-randomized-ROM')
        return folder,save,rom
    mac,mac_save,mac_rom=device('Mac');win,win_save,win_rom=device('Windows')
    def session(folder,save,rom):return CloudSession(access,save,rom,folder/'state')
    a=session(mac,mac_save,mac_rom);a.prepare()
    b=session(win,win_save,win_rom)
    try:b.prepare();raise AssertionError('Simultaneous second device was allowed')
    except CloudError:pass
    finally:b.release()
    a.finish()
    b=session(win,win_save,win_rom);b.prepare();b.finish()
    changed=bytearray(original);changed[-1]^=1;changed=bytes(changed)
    a=session(mac,mac_save,mac_rom);a.prepare();a.start();mac_save.write_bytes(changed)
    deadline=time.monotonic()+8
    while a.revision<2 and time.monotonic()<deadline:time.sleep(.1)
    assert a.revision==2,'Running game changes not uploaded'
    a.finish()
    b=session(win,win_save,win_rom);b.prepare()
    assert win_save.read_bytes()==changed,'Mac -> Windows handoff differs'
    assert next((win/'Cloud-Sicherungen').glob('*.sav')).read_bytes()==original
    newer=bytearray(changed);newer[-2]^=1;newer=bytes(newer)
    win_save.write_bytes(newer);b.finish()
    a=session(mac,mac_save,mac_rom);a.prepare()
    assert mac_save.read_bytes()==newer,'Windows -> Mac handoff differs'
    a.finish()
    offline=bytearray(original);offline[-3]^=1;mac_save.write_bytes(offline)
    different=bytearray(newer);different[-4]^=1;win_save.write_bytes(different)
    b=session(win,win_save,win_rom);b.prepare();b.finish()
    a=session(mac,mac_save,mac_rom)
    try:a.prepare();raise AssertionError('Divergent progress silently replaced')
    except CloudConflict:pass
    assert mac_save.read_bytes()==bytes(offline)
    a.prepare('cloud');a.finish()
    assert mac_save.read_bytes()==bytes(different)
    assert any(p.read_bytes()==bytes(offline) for p in (mac/'Cloud-Sicherungen').glob('*.sav'))
print('PASS actual clients: Mac -> Windows -> Mac, running-game upload, final upload, device lock, conflict and local backups')
