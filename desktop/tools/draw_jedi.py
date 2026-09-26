"""Hand-authored pixel-art source. No image model, API or game artwork.

Coordinates and silhouettes below are authored in logical pixels. Pillow only
rasterizes these shapes and writes previews; runtime needs no Pillow.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'jedi'
# name, skin, hair, robe, tabard, silhouette, blade, beard/armor
ROSTER = [
 ('Anakin Skywalker','#e6ae85','#704831','#303d58','#764445','swept','blue','armor'),
 ('Obi-Wan Kenobi','#e9b58d','#ac6035','#e7d7ad','#b59d72','swept','blue','beard-armor'),
 ('Ahsoka Tano','#de8954','#e0e4d7','#73474d','#91646b','togruta','green',''),
 ('Yoda','#91ad68','#d6d6af','#c8bd92','#8b7960','yoda','green',''),
 ('Mace Windu','#9b694e','#634537','#dac5a2','#82705b','bald','purple',''),
 ('Plo Koon','#c48b60','#a98763','#9a7754','#715039','kel-dor','blue','mask'),
 ('Kit Fisto','#70a977','#4d7d58','#d8be8b','#887555','nautolan','green',''),
 ('Aayla Secura','#6598c4','#517aab','#88734e','#665643','twilek','blue',''),
 ('Ki-Adi-Mundi','#e8be9f','#e0ded1','#d9caac','#8c6a4a','cerean','blue','beard'),
 ('Shaak Ti','#bf644e','#ddd7c6','#795141','#a8754c','togruta','blue',''),
 ('Luminara Unduli','#b2b18d','#3d3b40','#666151','#8d876b','hood','green',''),
 ('Barriss Offee','#b9b797','#393641','#384759','#536472','hood','blue',''),
 ('Pong Krell','#a88e76','#76645b','#82765e','#574e45','besalisk','green',''),
 ('Eeth Koth','#c4a174','#332f2c','#b4a080','#796144','horns','green','beard'),
 ('Adi Gallia','#976247','#d9c8a2','#b9a17c','#7d5945','tholothian','blue',''),
 ('Saesee Tiin','#bf9871','#8f6248','#b79c78','#77604a','horns','green',''),
 ('Even Piell','#c79587','#aa9a82','#b7a178','#7a6047','piell','green',''),
 ('Tera Sinube','#bfd4c5','#d2dad1','#c7c1a3','#8b8973','cosian','blue','beard'),
 ('Quinlan Vos','#b88b61','#292b2d','#64563f','#9d8b59','long','green','stripe'),
 ('Jocasta Nu','#ddba9f','#d8d8cf','#a84543','#cf9d63','bun','blue',''),
 ('Nahdar Vebb','#bd8156','#805438','#d8c69e','#917454','moncal','blue',''),
 ('Ima-Gun Di','#c3916d','#b69363','#c6b087','#8b6b49','horns','blue','beard'),
 ('Tiplar','#d0b565','#957c48','#977254','#c5a37a','mane','green',''),
 ('Tiplee','#ce897e','#a24d45','#98715a','#c4a580','mane','blue',''),
 ('Qui-Gon Jinn','#d0a582','#796044','#d4bf99','#8e7455','long','green','beard'),
 ('Sifo-Dyas','#c4b197','#cbc6b5','#b9ad95','#756b58','long','blue','beard'),
 ('Coleman Kcaj','#b9ac75','#8b794f','#cab48a','#87734f','ongree','green',''),
 ('Oppo Rancisis','#baae87','#dad5b9','#a49061','#736547','thub','green','beard'),
 ('Rig Nema','#bcb591','#777052','#d3c9a4','#9d9878','hood','green',''),
 ('Finn Ertay','#729c72','#516e56','#a58b65','#766449','twilek','green',''),
 ('Petro','#d7a276','#6e4630','#c7b991','#8b7659','swept','blue','young'),
 ('Katooni','#b49678','#d5cbb6','#c6b792','#8e795c','tholothian','blue','young'),
 ('Gungi','#957450','#624b34','#9d7c55','#745333','wookiee','green','young'),
 ('Ganodi','#99b398','#678768','#caba96','#8a775b','rodian','green','young'),
 ('Byph','#b0a794','#7b725e','#cabd9c','#8f7b5e','ithorian','green','young'),
 ('Zatt','#8aad73','#62884c','#c8bc9d','#8a775d','nautolan','green','young'),
 ('Halsey','#b59979','#d2c8a4','#d1bd95','#927858','ongree','green',''),
 ('Knox','#b08b6c','#493d32','#b6a582','#7d694f','long','blue','young'),
 ('Bolla Ropal','#83a393','#60745b','#b7a67f','#7b6b4b','rodian','green',''),
 ('Ord Enisence','#c4b398','#88806c','#c6b492','#827154','cosian','green',''),
 ('Tu-Anh','#c3987d','#423934','#b7b291','#7b856f','bun','blue',''),
 ('Depa Billaba','#ac805f','#343231','#9d795a','#cbb18b','bun','green',''),
 ('Caleb Dume','#c89972','#4b3d2f','#9e8562','#d0b28a','swept','blue','young'),
 ('Agen Kolar','#936244','#392d25','#c0a27c','#76553c','horns','green',''),
 ('Jedi-Tempelwache','#e8dfbb','#b8ad8a','#ddd1ae','#ae9568','guard','yellow',''),
]

def slug(name): return name.lower().replace(' ','-')
def shade(c, factor):
    return tuple(max(0,min(255,round(int(c[i:i+2],16)*factor))) for i in (1,3,5))
def palette(c):
    _, skin, hair, robe, tabard, _, blade, _ = c
    # Fixed semantic indices keep palette changes lossless across all poses.
    colors = [(0,0,0),(28,29,37),shade(skin,1),shade(skin,.75),shade(hair,1),
              shade(hair,1.28),shade(robe,1),shade(robe,.68),shade(tabard,1),
              (88,64,47),(190,200,200),(241,241,216),
              {'blue':(53,166,248),'green':(85,224,112),'purple':(183,91,236),'yellow':(247,206,72)}[blade],
              (220,253,255),(89,112,153),(49,45,42)]
    return colors

def head(d,c,x,y,back=False,side=False,large=False):
    """Hand-drawn 12px head with silhouette-specific alien anatomy."""
    kind,detail=c[5],c[7]
    def poly(p,col): d.polygon([(x+a,y+b) for a,b in p],fill=col)
    def rect(p,col): d.rectangle((x+p[0],y+p[1],x+p[2],y+p[3]),fill=col)
    poly([(2,1),(8,0),(11,3),(11,9),(8,12),(3,12),(0,8),(0,4)],1)
    poly([(2,3),(9,2),(10,5),(9,10),(7,11),(3,10),(1,7)],2)
    rect((8,5,9,9),3)
    if kind in ('swept','long','bun','mane'):
        poly([(0,7),(0,2),(3,0),(9,0),(11,3),(10,6),(8,4),(5,3),(2,5)],4)
        poly([(1,2),(4,1),(9,1),(7,2),(3,3)],5)
        if kind in ('long','mane'): rect((0,5,1,12),4);rect((10,4,11,12),4)
        if kind=='bun': rect((7,-2,10,1),4)
    elif kind=='hood':
        poly([(0,10),(0,2),(3,-1),(8,-1),(11,2),(12,11),(10,12),(9,3),(3,2),(2,11)],4)
    elif kind=='guard':
        poly([(0,10),(0,2),(3,-1),(8,-1),(11,2),(12,11),(9,12),(3,12)],8)
        poly([(2,3),(8,2),(10,5),(9,10),(6,12),(2,10)],11)
        rect((3,5,8,6),1);rect((5,8,6,10),8)
    elif kind in ('togruta','tholothian','twilek','nautolan','thub'):
        for px in (0,9): rect((px,3,px+2,14),4 if kind!='togruta' else 11)
        if kind=='togruta':
            poly([(0,4),(1,-3),(4,-1),(6,2),(8,-2),(10,-3),(12,5),(9,4),(6,3),(3,4)],11)
            rect((0,7,2,8),14);rect((9,10,11,11),14)
            rect((2,0,3,1),14);rect((8,0,9,1),14)
            rect((4,5,5,6),11);rect((7,5,8,6),11)
        elif kind=='tholothian': rect((1,1,10,3),11);rect((3,0,8,1),4)
        elif kind=='nautolan': rect((0,0,10,5),2);rect((1,1,2,2),3)
        elif kind=='thub': rect((-1,6,2,15),11);rect((8,7,12,15),11)
        else: rect((1,0,10,3),2)
    elif kind in ('yoda','piell'):
        poly([(-6,4),(1,5),(3,9),(-1,9)],2)
        poly([(10,5),(17,4),(12,9),(9,9)],2)
        rect((3,1,8,2),3)
    elif kind=='cerean':
        poly([(2,3),(2,-6),(4,-8),(7,-8),(9,-5),(10,4)],2)
        rect((3,-5,3,0),3)
    elif kind=='kel-dor':
        poly([(0,4),(1,0),(4,2),(8,0),(11,3),(10,9),(1,9)],2)
        rect((0,4,3,6),1);rect((7,4,10,6),1)
        rect((3,8,8,11),10);rect((5,8,6,11),1)
    elif kind=='horns':
        rect((1,1,9,3),4)
        for px in (1,5,9): poly([(px,-2),(px-1,2),(px+1,2)],11)
    elif kind=='cosian':
        poly([(0,3),(3,-1),(8,-1),(11,3),(10,10),(2,11)],2)
        poly([(3,7),(8,7),(7,13),(4,13)],3)
    elif kind=='moncal':
        poly([(0,3),(3,0),(8,0),(11,3),(12,7),(9,11),(2,11),(-1,7)],2)
        rect((-1,5,2,7),11);rect((9,5,12,7),11)
    elif kind=='ongree':
        poly([(-1,2),(2,0),(9,0),(12,3),(8,8),(8,12),(3,12),(2,8)],2)
        rect((1,1,2,3),1);rect((9,1,10,3),1)
    elif kind=='wookiee':
        poly([(0,3),(2,0),(9,1),(12,5),(11,12),(2,13),(-1,8)],4)
        rect((2,5,9,10),2);rect((4,10,7,12),5)
    elif kind=='rodian':
        rect((0,3,2,7),1);rect((9,3,11,7),1)
        rect((2,-2,3,0),2);rect((8,-2,9,0),2);rect((4,8,7,10),3)
    elif kind=='ithorian':
        poly([(-3,1),(12,0),(14,4),(11,7),(7,8),(7,12),(2,12),(2,7),(-3,5)],2)
        rect((-2,2,-1,3),1);rect((11,2,12,3),1)
    if back:
        if kind in ('swept','long','bun','mane'): rect((2,3,9,9),4);rect((3,4,7,6),5)
        else: rect((3,5,8,9),2)
    elif kind not in ('kel-dor','ithorian','ongree','guard'):
        if side: rect((1,6,2,7),1);rect((-1,8,1,9),2)
        else:
            rect((2,6,3,7),1);rect((8,6,9,7),1)
            if kind not in ('yoda','piell','rodian','moncal'): rect((2,5,4,5),4);rect((7,5,9,5),4)
            rect((5,9,6,9),3)
        if 'beard' in detail:
            poly([(2,9),(4,10),(7,10),(9,8),(9,11),(7,13),(4,12)],4)
            rect((4,10,7,10),5)
        if detail=='stripe': rect((1,8,9,8),8)

def overworld(c,direction,phase):
    im=Image.new('P',(32,32)); d=ImageDraw.Draw(im)
    short=c[5] in ('yoda','piell') or 'young' in c[7]
    y=4+(3 if short else 0); step=1 if phase==1 else -1 if phase==3 else 0
    side=direction in (2,3); back=direction==0
    # Narrow side silhouette, moving boot pairs; front/back keep body anchor.
    left,right=(11,18) if side else (9,20)
    d.rectangle((left+1,24,right-1,27),7)
    d.rectangle((left,26+max(step,0),left+4,29),15)
    d.rectangle((right-4,26+max(-step,0),right,29),15)
    d.line((left,29,left+4,29),fill=10);d.line((right-4,29,right,29),fill=10)
    d.polygon([(left,14+y//4),(right,14+y//4),(right+1,25),(left-1,25)],fill=1)
    d.polygon([(left+1,16),(right-1,16),(right,24),(left,24)],fill=6)
    d.polygon([(left+1,16),(left+4,16),(right-2,23),(left+1,24)],fill=8)
    d.rectangle((left,22,right,23),9);d.rectangle((14,22,15,23),10)
    d.rectangle((left-2,17,left,21),6);d.rectangle((right,17,right+2,21),6)
    if 'armor' in c[7]:
        d.rectangle((left-2,16,left,18),10);d.rectangle((right,16,right+2,18),10)
        d.point((left-1,16),fill=11);d.point((right+1,16),fill=11)
    # Lit saber occupies a reserved margin. Anatomical right is screen-left
    # in front view, screen-right in back view; right profile is mirrored.
    sx=23 if back else 6
    if side:sx=6
    d.rectangle((sx-1,4,sx+1,18),12);d.line((sx,4,sx,18),fill=13)
    d.rectangle((sx-1,19,sx+1,23),1);d.line((sx,19,sx,22),fill=10)
    handx=right+1 if back else left-1
    d.line((handx,20,sx,21),fill=2,width=2);d.point((sx,21),fill=3)
    head(d,c,9,y,back=back,side=side)
    if c[5]=='besalisk':
        d.line((9,23,6,25),fill=2,width=2);d.line((20,23,24,25),fill=2,width=2)
    if direction==3: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im

def battle(c,back=False,pose=0):
    """80x80 angular Clone-Wars-inspired stance, drawn in native pixels."""
    im=Image.new('P',(80,80));d=ImageDraw.Draw(im)
    short=c[5] in ('yoda','piell') or 'young' in c[7]
    # Cloth panels, split tabard, boots, bent sword arm; no traced game art.
    d.polygon([(27,47),(43,46),(49,68),(58,71),(57,76),(43,76),(37,59),(32,72),(32,76),(18,76),(18,72),(24,67)],fill=1)
    d.polygon([(28,50),(36,50),(31,69),(23,69)],fill=7)
    d.polygon([(37,49),(42,50),(47,68),(42,69)],fill=6)
    d.polygon([(23,69),(31,69),(30,73),(20,73)],fill=9)
    d.polygon([(43,68),(49,70),(55,72),(54,73),(44,73)],fill=9)
    d.line((21,74,30,74),fill=10);d.line((45,74,55,74),fill=10)
    d.polygon([(25,27),(32,23),(41,24),(49,31),(48,47),(43,58),(26,59),(23,45)],fill=1)
    d.polygon([(27,28),(33,25),(40,26),(46,32),(43,51),(28,54),(26,44)],fill=6)
    d.polygon([(28,28),(33,27),(42,44),(39,58),(32,58),(33,43)],fill=8)
    d.polygon([(39,27),(44,29),(44,42),(37,53),(33,54)],fill=7)
    d.polygon([(25,30),(21,31),(16,43),(17,49),(23,50),(29,34)],fill=1)
    d.polygon([(25,31),(23,33),(19,43),(21,46),(25,40),(28,33)],fill=6)
    d.polygon([(18,45),(22,46),(24,51),(20,54),(16,51)],fill=2)
    d.polygon([(43,29),(48,28),(53,37),(58,35),(61,41),(51,46),(47,41)],fill=1)
    d.polygon([(44,31),(47,31),(51,39),(56,38),(58,41),(51,43)],fill=6)
    if 'armor' in c[7]:
        d.polygon([(23,30),(27,28),(30,32),(25,35),(21,34)],fill=10)
        d.polygon([(43,29),(47,28),(51,32),(48,35),(44,34)],fill=10)
        d.line((24,30,27,30),fill=11);d.line((44,30,47,30),fill=11)
        d.polygon([(51,37),(55,35),(59,39),(55,42),(52,41)],fill=10)
    d.rectangle((25,43,44,46),9);d.rectangle((33,44,37,45),10)
    d.line((27,48,26,56),fill=8)
    # Two subtly different ready poses, both blade and hands remain in bounds.
    tip=(67+pose,5);hilt=(59,40)
    d.line((hilt[0],hilt[1],tip[0],tip[1]),fill=12,width=5)
    d.line((hilt[0],hilt[1],tip[0],tip[1]),fill=13,width=2)
    d.line((57,48,59,39),fill=1,width=5);d.line((57,47,59,40),fill=10,width=2)
    d.polygon([(54,40),(58,39),(61,42),(60,46),(56,46),(54,44)],fill=2)
    d.line((56,44,59,44),fill=3)
    # Explicit head pixels enlarged 2x without interpolation.
    hi=Image.new('P',(30,30));hd=ImageDraw.Draw(hi)
    head(hd,c,9,9,back=back)
    hi=hi.crop(hi.getbbox())
    factor=min(2,30/hi.height)
    hi=hi.resize((round(hi.width*factor),round(hi.height*factor)),Image.Resampling.NEAREST)
    mask=Image.new('L',hi.size);mask.putdata([255 if p else 0 for p in hi.getdata()])
    im.paste(hi,(34-hi.width//2,31-hi.height),mask)
    if back:
        d.polygon([(30,31),(37,29),(43,32),(40,41),(29,41)],fill=8)
        d.line((34,31,34,40),fill=7)
    if c[5]=='besalisk':
        d.line((26,39,13,52),fill=7,width=6);d.line((44,39,54,55),fill=7,width=6)
        d.rectangle((10,51,14,55),2);d.rectangle((52,54,57,58),2)
    if short:
        compact=im.crop((0,0,80,77)).resize((64,58),Image.Resampling.NEAREST)
        im=Image.new('P',(80,80));im.paste(compact,(8,19))
    return im

def encode(im):
    p=list(im.getdata())
    return bytes(p[i]|p[i+1]<<4 for i in range(0,len(p),2)).hex()
def rgba(im,colors):
    out=Image.new('RGBA',im.size)
    out.putdata([colors[p]+(255 if p else 0,) for p in im.getdata()]);return out

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    gallery=Image.new('RGB',(720,((len(ROSTER)+5)//6)*145),'#111a28');gd=ImageDraw.Draw(gallery)
    roster=[]
    for index,c in enumerate(ROSTER):
        colors=palette(c);frames=[overworld(c,r,k) for r in range(4) for k in range(4)]
        front=[battle(c,False,k) for k in range(2)];back=[battle(c,True,k) for k in range(2)]
        data={'format':2,'name':c[0],'size':32,'palette':[[round(v*31/255) for v in rgb] for rgb in colors],
              'frames':[encode(f) for f in frames],'front':[encode(f) for f in front],'back':[encode(f) for f in back]}
        name=slug(c[0]);(ROOT/f'{name}.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
        sheet=Image.new('RGBA',(128,128))
        for j,f in enumerate(frames):sheet.paste(rgba(f,colors),((j%4)*32,(j//4)*32))
        sheet.resize((512,512),Image.Resampling.NEAREST).save(ROOT/f'{name}-walk.png')
        rgba(front[0],colors).resize((320,320),Image.Resampling.NEAREST).save(ROOT/f'{name}-battle.png')
        x=(index%6)*120;y=(index//6)*145
        gallery.paste(rgba(front[0],colors),(x+20,y+5),rgba(front[0],colors))
        gallery.paste(rgba(frames[4],colors),(x+44,y+85),rgba(frames[4],colors))
        gd.text((x+4,y+121),c[0],fill='#dce6f2')
        roster.append({'id':name,'name':c[0]})
    (ROOT/'roster.json').write_text(json.dumps(roster,indent=2)+'\n')
    gallery.save(ROOT/'jedi-roster.png')
    print(f'Wrote {len(ROSTER)} hand-authored Jedi sprite sets to {ROOT}')

if __name__=='__main__':main()
