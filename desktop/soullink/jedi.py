"""Lossless, bounded graphics-only Clone Wars patch for German SoulSilver.

Archive indexes and DP picture cipher verified against pret/pokeheartgold.
Never changes game scripts, trainer parties, text or save files.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import struct
import sys
from pathlib import Path
from .cloud import atomic_write

PLAYERS = {'Optimus':'anakin-skywalker','Bee':'obi-wan-kenobi'}
ARCHIVES = ('a/0/8/1','a/0/5/8','a/0/0/6')
# The approved art sheets are ordered back, front, right, left. SoulSilver's
# field texture banks are back, front, left, right, so only the two side banks
# need to trade places. Keep this mapping here instead of altering the artwork.
GAME_TO_ART_DIRECTION = (0,1,3,2)

def _field_frame_index(texture_number):
    frame=(texture_number-1)%16
    direction,phase=divmod(frame,4)
    return GAME_TO_ART_DIRECTION[direction]*4+phase

def asset_root():
    return Path(getattr(sys,'_MEIPASS',Path(__file__).parents[1]))/'assets'/'jedi'

def roster():
    return json.loads((asset_root()/'roster.json').read_text())

def load_character(name):
    if name not in {r['id'] for r in roster()}:raise ValueError('Unbekannter Jedi.')
    data=json.loads((asset_root()/(name+'.json')).read_text())
    if data.get('format')!=2 or data.get('size')!=32 or len(data.get('palette',[]))!=16:
        raise ValueError('Ungültiges Jedi-Grafikpaket.')
    if any(len(rgb)!=3 or any(type(c)!=int or not 0<=c<32 for c in rgb) for rgb in data['palette']):
        raise ValueError('Ungültige Jedi-Farben.')
    for key,count,size in (('frames',16,512),('front',2,3200),('back',2,3200)):
        data[key]=[bytes.fromhex(v) for v in data[key]]
        if len(data[key])!=count or any(len(v)!=size for v in data[key]):raise ValueError('Ungültige Jedi-Animation.')
    return data

# Stable character identities for prominent named trainers. These pairs connect
# overworld texture names to the corresponding battle trainer-class indexes.
BOSSES = [
 (66,'gsleader1','plo-koon'),(67,'gsleader2','kit-fisto'),
 (70,'gsleader3','ahsoka-tano'),(72,'gsleader4','quinlan-vos'),
 (73,'gsleader7','yoda'),(74,'gsleader6','barriss-offee'),
 (75,'gsleader5','mace-windu'),(76,'gsleader8','shaak-ti'),
 (87,'gsbigfour1','ki-adi-mundi'),(112,'gsbigfour2','pong-krell'),
 (89,'gsbigfour3','saesee-tiin'),(88,'gsbigfour4','luminara-unduli'),
 (86,'wataru','qui-gon-jinn'),(98,'gsleader9','eeth-koth'),
 (103,'gsleader10','aayla-secura'),(104,'gsleader11','ima-gun-di'),
 (105,'gsleader12','tiplar'),(106,'gsleader13','katooni'),
 (107,'gsleader14','adi-gallia'),(108,'gsleader15','tera-sinube'),
 (110,'gsleader16','tiplee'),(109,'red','yoda'),
 (23,'gsrivel','ahsoka-tano'),(120,'minaki','nahdar-vebb'),
 (114,'rkanbuw','barriss-offee'),(116,'rkanbum','pong-krell'),
 (124,'sakaki','mace-windu'),
]

def assignments(player):
    if player not in PLAYERS:raise ValueError('Unbekannter Spieler.')
    others=[r['id'] for r in roster() if r['id'] not in PLAYERS.values()]
    battle={i:others[(i-2)%len(others)] for i in range(129)}
    battle[0]=PLAYERS[player]
    field={prefix:char for _,prefix,char in BOSSES}
    for cls,_,char in BOSSES:battle[cls]=char
    # Generic trainers share field graphics with some civilians in the game.
    generic={2:'boy1',3:'girl1',4:'campboy',5:'picnicgirl',6:'boy2',7:'woman1',
      9:'mount',10:'fighter',11:'fishing',12:'cyclem',13:'cyclew',14:'gsfighter',
      15:'artist',16:'man1',17:'woman2',18:'cowgirl',19:'sportsman',20:'bigman',
      22:'pikachu',24:'gorggeousm',25:'gorggeousw',26:'waitress',27:'man2',
      28:'babyboy1',29:'gsman1',30:'gsgirl1',31:'juggrer',32:'boy3',33:'lady',
      34:'gentleman',35:'middlewoman',36:'woman3',37:'mania',38:'policeman',
      39:'gsman2',40:'gswoman1',41:'assistantm',42:'gsswimmerm',43:'gsswimmerw',
      44:'gsbabyboy1',45:'gsbabygirl1',46:'seaman',47:'dancer',48:'explore',
      49:'man3',50:'gswoman2',51:'sunglasses',52:'gsman3',53:'gorggeousm',
      54:'gorggeousw',55:'rocketm',56:'skierw',57:'badman',58:'clown',
      59:'workman',60:'gsboy2',61:'gsgirl2',62:'rocketw',63:'thief',
      64:'fire',65:'gang',68:'mania',69:'boy2',71:'farmer',77:'gswoman3',
      78:'gsboy3',79:'bozu',80:'ambrella',81:'waiter',82:'itako',
      83:'cameraman',84:'reporter',85:'idol',97:'towerboss',99:'brains1',
      100:'brains2',101:'brains3',102:'brains4',111:'chourou',113:'doctor',
      115:'boarder',119:'man5'}
    for cls,prefix in generic.items():
        if prefix in field:battle[cls]=field[prefix]
        else:field[prefix]=battle[cls]
    for prefix in ('hero','rhero','pkthhero'):field[prefix]=PLAYERS[player]
    return battle,field

def _archive(original,name):
    from ndspy.fnt import load
    fnt,nf,fat,na=struct.unpack_from('<4I',original,0x40)
    if fnt+nf>len(original) or fat+na>len(original):raise ValueError('Ungültige ROM-Dateitabelle.')
    fid=load(original[fnt:fnt+nf]).idOf(name)
    if fid is None or fid*8+8>na:raise ValueError('Trainer-Grafikarchiv fehlt: '+name)
    start,end=struct.unpack_from('<II',original,fat+fid*8)
    if not 0<=start<end<=len(original):raise ValueError('Ungültige Archivgrenzen.')
    a=original[start:end]
    if a[:4]!=b'NARC' or a[16:20]!=b'BTAF':raise ValueError('Ungültiges Trainer-Archiv.')
    table_size,count=struct.unpack_from('<II',a,20)
    names=16+table_size;payload=names+struct.unpack_from('<I',a,names+4)[0]+8
    if a[payload-8:payload-4]!=b'GMIF' or 28+count*8>len(a):raise ValueError('Ungültige Archivtabelle.')
    spans=[]
    for i in range(count):
        lo,hi=struct.unpack_from('<II',a,28+i*8);lo+=payload;hi+=payload
        if not payload<=lo<=hi<=len(a):raise ValueError('Ungültige Grafikgrenzen.')
        spans.append((start+lo,start+hi))
    return spans

def _field(data,skin):
    from ndspy.texture import NSBTX,TextureFormat
    texture=NSBTX(data);out=bytearray(data)
    if len(texture.textures) not in (16,32) or len(texture.palettes)!=1:
        raise ValueError('Unbekannte Laufanimation.')
    tex0=struct.unpack_from('<I',out,16)[0]
    capacity,info=struct.unpack_from('<HH',out,tex0+12)
    pixels=tex0+struct.unpack_from('<I',out,tex0+20)[0]
    pal=tex0+struct.unpack_from('<I',out,tex0+56)[0]
    entries=tex0+info+16+4*len(texture.textures)
    if pixels+capacity*8>len(out) or pal+32>len(out):raise ValueError('Ungültige Texturgrenzen.')
    unique={};expected=[]
    for i,(name,t) in enumerate(texture.textures):
        match=re.search(r'\.(\d+)$',name)
        if not match or t.size!=(32,32) or t.format!=TextureFormat.I4:raise ValueError('Unbekanntes Figurenformat.')
        frame=skin['frames'][_field_frame_index(int(match[1]))]
        if frame not in unique:unique[frame]=len(unique)*512
        offset=unique[frame]
        if offset+512>capacity*8:raise ValueError('Jedi-Animation ist zu groß.')
        out[pixels+offset:pixels+offset+512]=frame
        struct.pack_into('<H',out,entries+i*8,offset//8);expected.append(frame)
    out[pixels+len(unique)*512:pixels+capacity*8]=bytes(capacity*8-len(unique)*512)
    out[pal:pal+32]=palette_bytes(skin)
    if [t.data1 for _,t in NSBTX(out).textures]!=expected:raise ValueError('Jedi-Texturprüfung fehlgeschlagen.')
    return bytes(out)

def palette_bytes(skin):
    return struct.pack('<16H',*(r|(g<<5)|(b<<10) for r,g,b in skin['palette']))

def _dp_cipher(data):
    """DP-direction picture XOR; final plaintext word must be transparent."""
    if len(data)!=6400 or data[-2:]!=b'\0\0':raise ValueError('Ungültige Kampf-Bilddaten.')
    words=list(struct.unpack('<3200H',data));seed=0x5A17
    for i in range(3199,-1,-1):
        words[i]^=seed&0xFFFF;seed=(seed*1103515245+24691)&0xFFFFFFFF
    return struct.pack('<3200H',*words)

def _sprite_tiles(cells,frames,length):
    # Nitro cell bank stores packed OAM rectangles, not a plain 10x10 tile grid.
    # Preserve animation cells and VRAM-transfer slots, fill each exact shape.
    if cells[:4]!=b'RECN' or cells[16:20]!=b'KBEC':raise ValueError('Ungültige Kampfzellen.')
    count,flags,table,mapping,transfer=struct.unpack_from('<HHIII',cells,24)
    if flags!=1 or mapping>3 or not 1<=count<=32:raise ValueError('Unbekannte Kampfzellen.')
    table+=24;stride=16;oams=table+count*stride;transfer+=24
    array=transfer+struct.unpack_from('<I',cells,transfer+4)[0]
    dims=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
    out=bytearray(length)
    for ci in range(count):
        n,_,offset=struct.unpack_from('<HHI',cells,table+ci*stride)
        if n==0:continue
        base,size=struct.unpack_from('<II',cells,array+ci*8)
        if base+size>length:raise ValueError('Kampf-VRAM liegt außerhalb der Grafik.')
        objects=[]
        for oi in range(n):
            a,b,c=struct.unpack_from('<HHH',cells,oams+offset+oi*6)
            if a&0x300 or a>>14==3:raise ValueError('Unbekanntes Kampfobjekt.')
            x=b&511;x=x-512 if x>=256 else x
            y=a&255;y=y-256 if y>=128 else y
            w,h=dims[a>>14][b>>14]
            objects.append((x,y,w,h,b,c))
        minx=min(o[0] for o in objects);miny=min(o[1] for o in objects)
        frame=frames[ci%2]
        for x,y,w,h,attr,char in objects:
            start=base+(char&1023)*(32<<mapping)
            if start+w*h//2>base+size:raise ValueError('Kampfobjekt ist zu groß.')
            for ty in range(h//8):
                for tx in range(w//8):
                    for py in range(8):
                        for px in range(0,8,2):
                            pair=[]
                            for p in (px,px+1):
                                dx=tx*8+p;dy=ty*8+py
                                if attr&0x1000:dx=w-1-dx
                                if attr&0x2000:dy=h-1-dy
                                fx=x-minx+dx;fy=y-miny+dy
                                value=frame[fy*40+fx//2] if 0<=fx<80 and 0<=fy<80 else 0
                                pair.append((value>>(4*(fx%2)))&15)
                            pos=start+(ty*(w//8)+tx)*32+py*4+px//2
                            out[pos]=pair[0]|pair[1]<<4
    return bytes(out)

def _battle(files,skin,back=False):
    pixels,pal,cells,anim,picture=files
    if pixels[:4]!=b'RGCN' or picture[:4]!=b'RGCN' or pal[:4]!=b'RLCN':
        raise ValueError('Unbekanntes Kampfgrafikformat.')
    if not 48<len(pixels)<=40000 or len(picture)!=6448 or len(pal)!=552:
        raise ValueError('Unbekannte Kampfanimationsgröße.')
    frames=skin['back' if back else 'front']
    # Bitmap picture: two 80x80 poses interleaved as a 160x80 raster.
    wide=b''.join(frames[0][y*40:(y+1)*40]+frames[1][y*40:(y+1)*40] for y in range(80))
    # Some animated trainers (e.g. the Castle Valet) select palette bank 1.
    # Populate every bank so no pose falls back to the previous trainer colors.
    p=bytearray(pal);p[40:552]=palette_bytes(skin)*16
    tiles=_sprite_tiles(cells,frames,len(pixels)-48)
    return (pixels[:48]+tiles,bytes(p),cells,anim,picture[:48]+_dp_cipher(wide))

def patch_rom_bytes(original,player):
    if original[:16]!=b'POKEMON SS\0\0IPGD':raise ValueError('Jedi-Paket benötigt deutsche SoulSilver-ROM.')
    battle,field=assignments(player);spans={n:_archive(original,n) for n in ARCHIVES}
    if len(spans[ARCHIVES[1]])!=645 or len(spans[ARCHIVES[2]])!=85:
        raise ValueError('Unbekannte Trainer-Grafikversion.')
    cache={name:load_character(name) for name in set(battle.values())|set(field.values())}
    out=bytearray(original);changed=[]
    from ndspy.texture import NSBTX
    for index,(lo,hi) in enumerate(spans[ARCHIVES[0]]):
        chunk=original[lo:hi]
        if chunk[:4]!=b'BTX0':continue
        t=NSBTX(chunk)
        if not t.textures:continue
        prefix=t.textures[0][0].rsplit('.',1)[0]
        if prefix not in field or len(t.textures) not in (16,32):continue
        out[lo:hi]=_field(chunk,cache[field[prefix]]);changed.append((ARCHIVES[0],index,field[prefix]))
    for name,back in ((ARCHIVES[1],False),(ARCHIVES[2],True)):
        for i in range(len(spans[name])//5):
            char=PLAYERS[player] if back and i in (0,15) else battle.get(i,'ahsoka-tano')
            if char not in cache:cache[char]=load_character(char)
            selected=spans[name][i*5:i*5+5]
            replacements=_battle([original[lo:hi] for lo,hi in selected],cache[char],back)
            for (lo,hi),replacement in zip(selected,replacements):
                if len(replacement)!=hi-lo:raise ValueError('Grafikgröße hat sich verändert.')
                out[lo:hi]=replacement
            changed.append((name,i,char))
    if not any(n==ARCHIVES[0] and c==PLAYERS[player] for n,_,c in changed):
        raise ValueError('Die Spielerfigur wurde nicht gefunden.')
    if len(out)!=len(original):raise ValueError('ROM-Größe hat sich verändert.')
    return bytes(out),changed

def rom_identity(rom):
    """Retain cloud identity across a verified graphics-only edit.

    Sidecar is portable with the round. It is honored only for its exact current
    ROM bytes, never after another randomization or unrelated edit.
    """
    actual=hashlib.sha256(rom.read_bytes()).hexdigest()
    sidecar=rom.with_suffix('.graphics-identity.json')
    try:
        data=json.loads(sidecar.read_text())
        if data['current']==actual and re.fullmatch(r'[a-f0-9]{64}',data['original']):return data['original']
    except (OSError,ValueError,KeyError,TypeError):pass
    return actual

def apply_jedi(rom:Path,player,*,backup=True):
    original=rom.read_bytes();patched,report=patch_rom_bytes(original,player)
    if patched==original:return False
    identity=rom_identity(rom)
    if backup:
        recovery=rom.with_suffix('.pre-jedi.nds')
        try:
            with recovery.open('xb') as f:f.write(original);f.flush();os.fsync(f.fileno())
        except FileExistsError:pass
    metadata={'format':1,'original':identity,'current':hashlib.sha256(patched).hexdigest()}
    # Sidecar first: if interrupted before ROM replacement, its hash does not
    # match and the original ROM identity is still used.
    atomic_write(rom.with_suffix('.graphics-identity.json'),json.dumps(metadata).encode())
    atomic_write(rom,patched)
    return True
