"""Version-independent input profiles, isolated by local player and computer."""
import json
import re
import tomllib
from pathlib import Path
from .cloud import atomic_write

def validated(value):
    result={}
    for table in ('Keyboard','Joystick'):
        mapping=value.get(table,{})
        if not isinstance(mapping,dict):raise ValueError('Invalid input mapping')
        result[table]={key:number for key,number in mapping.items()
            if isinstance(key,str) and re.fullmatch(r'[A-Za-z0-9_]+',key)
            and type(number) is int and -(1<<31)<=number<(1<<31)}
    joystick=value.get('JoystickID',0)
    result['JoystickID']=joystick if type(joystick) is int and 0<=joystick<256 else 0
    return result

def read_native(path):
    return validated(tomllib.loads(path.read_text(encoding='utf-8'))['Instance0'])

def profile_path(root,player):
    if player not in ('Optimus','Bee'):raise ValueError('Unknown local player')
    return root/'Controls'/(player+'.json')

def load_profile(root,player):
    """Recover the newest valid profile, including configurations from older builds.

    Native input dialogs save immediately. This also recovers settings when an
    older launcher exited before importing them. Never touch these source files.
    """
    path=profile_path(root,player)
    candidates=[path,path.with_suffix('.previous.json'),*((root/'Emulator'/player).glob('build-*/portable/melonDS.toml'))]
    candidates=[p for p in candidates if p.is_file()]
    for source in sorted(candidates,key=lambda p:p.stat().st_mtime_ns,reverse=True):
        try:
            value=validated(json.loads(source.read_text(encoding='utf-8'))) if source.suffix=='.json' else read_native(source)
            if value['Keyboard'] or value['Joystick']:return value
        except (OSError,ValueError,KeyError,TypeError,AttributeError):continue
    return validated({})

def save_profile(root,player,value):
    path=profile_path(root,player);value=validated(value)
    if path.exists():atomic_write(path.with_suffix('.previous.json'),path.read_bytes())
    atomic_write(path,json.dumps(value,indent=2).encode())

def key_label(value):
    from .melonds import QT_KEYS
    reverse={number:name for name,number in QT_KEYS.items()}
    return reverse.get(value,chr(value) if 32<=value<=126 else 'QT:'+str(value))
