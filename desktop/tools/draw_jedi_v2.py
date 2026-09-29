"""Native pixel source for the approved Clone Wars revision (45 characters).

Shared line weight, three-tone shading and proportions; species-specific heads,
costumes and silhouettes. Plo and Yoda retain the exact approved front pixels.
No downloaded artwork, image API or ROM is used by this development tool.
"""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from draw_jedi import ROSTER, slug, shade, encode
from jedi_approved import plo, yoda, Sprite

ROOT=Path(__file__).resolve().parents[1]/'assets'/'jedi'


def colors(c):
    skin,hair,robe,tabard=c[1:5]
    return [(0,0,0),(36,38,48),shade(robe,.48),shade(robe,.72),shade(robe,1),
            shade(tabard,1.12),shade(skin,.68),shade(skin,1),shade(skin,1.20),
            shade(hair,1),shade(hair,.62),shade(hair,1.35),(17,27,35),
            {'blue':(66,185,237),'green':(92,207,105),'purple':(188,107,241),'yellow':(243,202,80)}[c[6]],
            (223,251,242),(238,215,166)]


def palette_of(im):
    rgb=im.getpalette()
    return [tuple(rgb[i:i+3]) for i in range(0,48,3)]


def set_colors(im,pal):
    im.putpalette([v for rgb in pal for v in rgb]+[0]*720)
    im.info['transparency']=0
    return im


def face(s,c,back=False):
    """24px faces, authored natively, not enlarged 12px templates."""
    p,r,l=s.p,s.r,s.l
    kind,detail=c[5],c[7]
    # Shared jaw only for humanoids; aliens override it below.
    p(1,34,7,42,6,48,9,50,14,49,23,45,29,39,31,33,28,30,22,30,14)
    p(6,34,9,41,8,47,11,48,16,47,23,44,27,39,29,34,26,32,21,32,15)
    p(7,35,10,42,9,46,12,46,19,43,24,39,27,35,25,33,21,33,15)
    p(8,35,11,40,10,42,12,40,16,35,16,33,15)
    p(6,31,18,33,19,33,23,31,22);p(6,47,18,49,17,50,21,47,23)
    if kind in ('swept','long','bun','mane'):
        p(1,29,19,29,13,31,8,38,4,45,5,50,10,51,18,47,24,45,20,46,15,40,13,35,16,32,18)
        p(9,30,16,31,10,38,6,44,7,48,10,49,16,47,20,46,13,41,12,35,15)
        p(11,32,11,38,7,43,8,41,10,35,12)
        l(10,37,12,43,10,47,13)
        if c[0]=='Anakin Skywalker':
            p(9,46,18,49,17,49,26,46,29,45,25,46,22)
            p(9,30,17,33,17,32,24,34,27,31,26,29,23)
            l(6,44,17,45,20,44,23) # scar
        if kind in ('long','mane'):
            p(9,30,15,33,17,32,27,34,32,28,32,29,22)
            p(9,47,15,50,16,50,27,53,32,46,31,47,25)
            l(11,30,19,30,28);l(10,49,20,48,29)
        if kind=='bun':
            p(1,42,5,42,2,46,1,50,3,50,7,47,10)
            p(9,44,4,46,2,49,4,48,7,45,7)
    elif kind=='hood':
        p(1,28,32,28,12,31,6,39,3,46,5,51,12,53,33,47,32,46,14,41,10,35,12,33,29)
        p(9,29,29,30,12,34,7,40,5,45,7,49,13,51,31,48,28,47,12,41,8,34,10,32,18,31,29)
        l(11,31,13,34,8,39,6)
        if c[0]=='Luminara Unduli':
            r(10,32,11,47,13);l(11,34,11,44,11);r(10,36,26,44,28)
    elif kind in ('twilek','nautolan','togruta','tholothian','thub'):
        if kind in ('twilek','nautolan'):
            for x in (28,48):
                p(1,x,13,x+5,11,x+6,22,x+4,32,x+6,36,x+2,37,x,33)
                p(6,x+1,15,x+4,14,x+4,23,x+2,32,x+4,35,x+2,34)
                l(7,x+2,16,x+3,22,x+1,29)
            if kind=='nautolan':
                for x in (25,52):
                    p(6,x,16,x+3,13,x+3,25,x+1,34,x-1,32,x+1,23)
                p(7,31,15,32,9,38,5,44,6,48,10,48,15)
        else:
            for x in (28,47):
                p(1,x,12,x+5,12,x+7,33,x+4,38,x,34)
                p(15,x+1,14,x+4,14,x+5,33,x+3,35,x+1,30)
                p(10,x+1,22,x+5,25,x+5,29,x+1,26)
                l(10,x+2,32,x+4,33)
            if kind=='togruta':
                p(1,27,16,28,7,31,0,35,2,39,9,43,7,47,0,51,5,53,16,47,14,42,11,35,12)
                p(15,29,13,30,7,32,2,35,6,38,11,43,9,47,3,50,7,51,13,46,11,42,10,35,11)
                p(10,30,7,33,5,35,8,30,10);p(10,46,6,49,6,50,9,45,8)
                p(15,35,15,38,17,36,19,34,18);p(15,42,16,45,14,46,17,43,19)
                l(15,37,24,39,25,41,24)
            elif kind=='tholothian':
                p(10,30,13,31,7,36,4,44,5,49,8,50,13)
                p(15,31,10,35,7,43,7,48,10,47,12,33,12)
                l(9,33,9,46,10)
            else:
                p(11,28,16,32,15,33,25,36,30,42,31,47,27,49,18,53,20,52,32,45,37,34,37,28,31)
    elif kind=='cerean':
        p(1,31,15,32,4,36,0,43,0,47,5,48,15)
        p(7,33,14,34,5,37,1,42,1,45,5,46,14)
        p(8,35,6,37,2,40,2,40,8,38,13,34,13)
        l(6,34,12,44,12);l(6,35,9,43,9)
        l(11,30,15,31,22);l(11,48,15,48,22)
    elif kind=='horns':
        p(9,31,16,31,9,35,6,45,7,49,12,49,17,45,13,37,12)
        if c[0]=='Saesee Tiin':
            for x in (28,48):p(1,x,8,x+3,6,x+4,17,x+2,26,x-1,25,x+1,17)
            for x in (29,49):p(6,x,9,x+1,10,x+2,18,x,23,x+1,16)
        else:
            for x,y in ((32,9),(37,7),(43,8),(48,11)):
                p(1,x-1,y+1,x,y-4,x+3,y+2);p(15,x,y-2,x,y+1,x+1,y+1)
    elif kind=='moncal':
        p(1,30,26,27,20,28,12,32,6,39,4,47,8,51,14,52,22,48,28,37,30)
        p(7,31,25,29,20,30,13,34,8,40,6,46,10,49,15,49,22,46,26,38,28)
        p(8,33,12,36,8,41,8,45,12,43,15,35,15)
        p(6,34,20,43,20,46,25,42,29,36,27)
        for x in (28,46):
            p(1,x,16,x+3,14,x+6,17,x+5,22,x+1,23,x-1,20)
            r(15,x+1,17,x+4,20);r(12,x+2,17,x+3,20)
        l(1,37,25,43,25)
    elif kind=='rodian':
        for x in (33,45):r(6,x,4,x+2,9);r(7,x,3,x+2,5)
        p(6,33,13,39,8,45,12,47,20,44,26,40,28,35,25)
        for x in (31,43):
            p(1,x,15,x+4,13,x+6,15,x+5,21,x+1,22,x-1,19)
            p(12,x+1,15,x+3,14,x+4,16,x+3,20,x+1,20)
            r(15,x+1,15,x+1,16)
        p(7,37,22,41,21,45,24,43,27,38,27,35,25);r(6,40,24,43,25)
    elif kind=='ithorian':
        r(0,27,4,53,31)
        p(1,23,8,29,5,48,5,54,9,55,16,50,20,45,20,44,30,33,31,31,22,25,19,23,16)
        p(7,25,10,30,7,47,7,52,10,53,15,49,18,43,18,42,28,35,29,33,20,27,17)
        p(8,27,10,32,8,45,8,50,11,48,13,30,13)
        p(6,26,14,32,17,37,20,37,27,34,26,32,21,27,18)
        r(12,26,11,28,13);r(12,49,11,51,13)
        l(6,36,13,43,14,46,13)
    elif kind=='ongree':
        p(6,29,11,34,7,43,7,49,12,45,20,44,28,36,29,34,20)
        p(7,32,12,35,9,42,9,46,12,41,20,41,26,37,26,36,18)
        for x in (28,47):
            r(6,x,19,x+2,24);r(12,x-1,23,x+3,25);r(8,x,23,x+1,23)
        p(10,35,10,42,10,44,13,41,15,36,14)
    elif kind=='wookiee':
        p(10,29,13,32,6,39,4,47,7,51,15,49,29,44,34,34,33,29,28)
        p(9,31,15,33,8,40,6,45,9,48,16,46,27,42,31,35,30,31,25)
        p(7,34,17,43,16,46,20,44,26,36,27,32,23)
        for x in (32,36,43,47):l(11,x,12,x-1,16)
    elif kind in ('cosian','besalisk'):
        p(7,30,16,32,9,36,5,44,7,49,13,48,22,44,27,37,28,31,23)
        if kind=='cosian':
            p(6,34,19,45,19,46,25,40,29,34,27,31,23)
            p(8,35,20,42,20,43,22,40,24,34,23)
        else:
            p(6,29,23,34,21,45,22,49,26,45,31,34,31,29,27)
            p(7,30,23,35,23,41,25,46,25,44,28,35,29)
            for x in (34,39,44):p(6,x,7,x,2,x+3,5,x+4,9)
    elif kind=='piell':
        p(7,20,15,30,18,32,24,27,22);p(7,48,18,59,13,54,22,48,24)
        p(9,37,8,38,3,41,1,43,4,42,9)
    elif kind=='guard':
        p(10,29,31,28,12,33,4,44,4,51,11,53,32,46,32,44,12,35,13,33,31)
        p(15,33,12,39,9,45,12,47,20,43,28,38,30,33,24)
        p(9,34,14,39,12,44,14,42,16,37,16)
        l(12,34,18,37,19);l(12,41,19,44,18);l(9,39,21,39,26)
    if not back and kind not in ('guard','ithorian','ongree','moncal','rodian'):
        # Directional eyebrows and softly shaded eye sockets.
        l(6,33,18,36,17,38,18);l(6,42,18,45,17,47,18)
        l(12,34,19,37,19);l(12,43,19,46,19)
        r(15,34,19,34,19);r(15,43,19,43,19)
        l(6,40,19,39,23,41,23);l(6,37,26,42,26)
        if kind=='nautolan':
            p(12,33,17,37,17,38,19,36,22,33,21);p(12,42,17,46,17,47,19,45,22,42,21)
            r(15,34,18,34,18);r(15,43,18,43,18)
        if kind=='piell':r(6,33,18,37,21);l(10,34,16,36,23)
        if 'beard' in detail:
            p(9,33,23,36,25,39,24,42,25,46,23,45,28,41,32,36,30)
            l(11,35,26,38,27,42,27,44,25);l(6,38,25,41,25)
        if detail=='stripe':r(15,32,21,47,22)
        if c[0]=='Barriss Offee':
            for x,y in ((34,23),(36,24),(43,24),(45,23)):r(10,x,y,x,y)
        if c[0]=='Mace Windu':l(6,34,14,38,15);l(6,42,15,46,14)
    if back:
        # Rear skull has no eyes/mouth. Preserve species silhouette/accessories.
        fill=9 if kind in ('swept','long','bun','mane','hood','wookiee','guard','tholothian') else 7
        p(fill,34,12,43,11,46,15,46,24,42,29,36,28,33,23,33,16)
        l(10 if fill==9 else 6,43,15,44,23,41,27)
        if kind=='togruta':
            p(15,34,12,43,12,47,22,44,32,37,34,33,27)
            p(10,34,16,44,18,46,22,35,21);p(10,35,26,45,27,43,30,36,30)


def humanoid(c,back=False):
    s=plo() # approved body construction, with a new species-specific head
    pal=colors(c);set_colors(s.im,pal)
    s.r(0,26,0,54,33)
    s.p(2,27,32,32,28,42,28,49,33,46,36,31,36)
    # Costume adaptations retain consistent limb anchors.
    if 'armor' in c[7]:
        s.p(1,23,33,27,30,32,33,29,38,22,37)
        s.p(15,24,33,27,32,30,34,28,36,23,35)
        s.p(1,47,31,51,32,54,36,50,38,46,35)
        s.p(15,48,32,51,33,52,35,49,36,47,34)
        s.p(15,54,44,57,43,60,46,57,49,55,47)
    if c[0]=='Ahsoka Tano':
        s.p(7,23,36,26,37,23,47,21,51,18,50,21,40)
        s.p(7,49,36,52,38,54,46,57,45,58,48,54,50,51,46)
        s.p(2,30,52,35,51,36,63,30,65,29,60)
        s.p(2,39,52,44,53,46,63,41,65,38,59)
        s.p(8,32,41,41,41,41,45,32,45)
    if c[0]=='Aayla Secura':
        s.p(7,23,35,26,37,23,49,20,53,18,49,21,39)
        s.p(7,49,35,52,37,54,46,58,45,59,48,54,50,51,45)
        s.p(7,32,42,43,42,43,45,31,45)
    if c[5]=='besalisk':
        s.p(1,24,40,28,42,22,53,17,56,12,54,13,50,19,48)
        s.p(3,24,42,26,43,20,52,16,54,14,52,20,49)
        s.p(7,12,51,15,52,15,56,11,57,9,55,10,52)
        s.p(1,48,43,51,43,56,54,63,55,63,60,55,61,49,53)
        s.p(3,49,45,51,45,56,56,60,56,60,59,55,59,51,51)
        s.p(7,60,55,65,55,66,59,62,61,60,59)
        s.l(13,65,55,75,34,width=3);s.l(14,65,55,75,34)
    if c[5]=='thub':
        s.r(0,22,62,59,75)
        s.p(1,29,60,47,60,54,66,64,66,67,62,71,63,69,70,62,75,32,75,24,70)
        s.p(6,30,62,45,62,52,69,63,69,68,66,65,71,59,73,32,73,27,69)
        s.l(8,32,64,42,65,47,69,54,71)
    if c[5]=='wookiee':
        for x,y in ((26,38),(28,55),(45,53),(32,66),(46,66)):s.l(11,x,y,x-1,y+4)
    face(s,c,back)
    if back:
        s.p(3,31,33,40,32,46,36,43,46,45,62,32,63,33,45)
        s.l(2,39,36,38,46,40,60);s.l(4,33,36,35,41)
        s.r(2,31,47,44,49)
    if 'young' in c[7] or c[5]=='piell':
        compact=s.im.crop((0,0,80,76)).resize((65,61),Image.Resampling.NEAREST)
        s.im=Image.new('P',(80,80));set_colors(s.im,pal);s.im.paste(compact,(7,15))
    return s.im


def battle(c,back=False,pose=0):
    if c[5] in ('kel-dor','yoda'):
        s=plo() if c[5]=='kel-dor' else yoda()
        if back and c[5]=='kel-dor':
            s.p(6,30,12,35,7,43,6,49,12,49,23,43,30,36,30,30,23)
            s.p(7,31,13,36,8,42,8,46,12,46,22,41,27,35,25,31,21)
            s.l(8,35,10,34,17,36,22);s.l(6,41,11,43,17,42,24)
            s.p(3,30,33,39,31,45,34,44,47,47,65,31,65,34,46);s.l(2,39,35,38,61)
        elif back:
            s.p(3,29,34,33,29,39,28,45,31,48,36,47,43,41,49,34,47,29,42)
            s.p(4,30,35,34,30,39,29,44,32,46,37,44,44,39,47,33,44,30,41)
            s.l(5,34,32,37,30,41,32);s.l(3,41,35,44,39,42,44)
            s.p(10,30,50,43,49,47,56,49,72,27,72,30,61)
            s.p(11,32,52,40,51,43,56,43,69,30,70,33,60);s.l(9,40,56,39,68)
        im=s.im
    else:im=humanoid(c,back)
    if pose:
        # Small blade sway without moving the feet or changing the approved pose.
        crop=im.crop((66,2,78,36));im.paste(0,(66,2,78,36));im.paste(crop,(65,2))
    return im


def overworld(c,direction,phase):
    front=battle(c);pal=palette_of(front)
    # Per-character palette mapping lets accepted alien colors stay lossless.
    base=colors(c)
    lut=[0]+[min(range(1,16),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,pal[i]))) for rgb in base[1:]]
    if c[5]=='yoda':lut=[0,1,9,10,11,8,3,4,5,10,9,11,13,14,15,12]
    im=Image.new('P',(32,32));set_colors(im,pal);d=ImageDraw.Draw(im)
    def p(color,points):d.polygon(points,fill=lut[color])
    def r(color,box):d.rectangle(box,fill=lut[color])
    def l(color,*xy):d.line(list(zip(xy[::2],xy[1::2])),fill=lut[color])
    side=direction in (2,3);back=direction==0;short=c[5] in ('yoda','piell') or 'young' in c[7]
    step=1 if phase==1 else -1 if phase==3 else 0
    left,right=(12,20) if side else (10,22)
    r(1,(left,24,right,28));r(2,(left,27+max(step,0),left+4,30));r(2,(right-4,27+max(-step,0),right,30))
    r(4,(left,29+max(step,0),left+3,29+max(step,0)));r(4,(right-3,29+max(-step,0),right,29+max(-step,0)))
    p(1,[(left,14),(right,14),(right+2,27),(left-2,27)])
    p(3,[(left+1,15),(right-1,15),(right+1,26),(left-1,26)])
    p(4,[(left,16),(left+3,15),(left+2,25),(left-1,26)])
    if not back:p(5,[(14,15),(19,15),(19,23),(21,26),(14,26),(15,22)])
    r(2,(left,22,right,23))
    if not back:r(15,(16,22,17,23))
    r(3,(left-2,17,left,22));r(3,(right,17,right+2,22))
    if 'armor' in c[7]:r(15,(left-2,16,left+1,18));r(15,(right-1,16,right+2,18))
    sx=26 if back else 5
    r(13,(sx-1,6 if short else 3,sx+1,20));r(14,(sx,6 if short else 3,sx,20))
    r(1,(sx-1,21,sx+1,24));r(15,(sx,21,sx,23))
    r(7,(sx-1,22,sx+2,23));r(7,(right+1,22,right+2,24))
    # Use the new head designs as a pixel reference at native field scale.
    src=battle(c,back)
    box=(8,26,67,51) if c[5]=='yoda' else (23,0,56,34)
    if 'young' in c[7] or c[5]=='piell':box=(24,15,54,43)
    head=src.crop(box)
    if c[5]=='yoda':
        # The wide ear crop touches the nearby saber. It is not part of the head.
        head.putdata([0 if v in (14,15) else v for v in head.getdata()])
    width,height=(25,11) if c[5]=='yoda' else (16,16)
    if side:
        head=head.crop((head.width//5,0,head.width-head.width//5,head.height));width=12
    head=head.resize((width,height),Image.Resampling.NEAREST)
    if side and not back:
        # A single visible eye and projecting profile; no two-eyed side faces.
        hd=ImageDraw.Draw(head);skin=lut[7]
        hd.rectangle((6,6,10,11),fill=skin);hd.point((2,8),fill=lut[12])
    mask=Image.new('L',head.size);mask.putdata([255 if v else 0 for v in head.getdata()])
    im.paste(head,(16-width//2,9 if short else 2),mask)
    # Player characters use dedicated native 32 px faces from the approved
    # John/Eddie sheet. This avoids the generic battle-head downscale that
    # made both overworld figures look alike.
    if c[0] in ('Anakin Skywalker','Obi-Wan Kenobi'):
        d.rectangle((7,1,24,16),fill=0)
        obi=c[0]=='Obi-Wan Kenobi';hair=9;hair_dark=10;hair_light=11
        skin=7;skin_shadow=6;skin_light=8;ink=1
        if back:
            p(ink,[(9,6),(11,2),(16,1),(21,3),(23,7),(22,13),(19,16),(12,15),(9,12)])
            p(hair,[(10,7),(12,3),(16,2),(20,4),(22,7),(21,12),(18,15),(13,14),(10,11)])
            p(hair_light,[(12,4),(16,2),(19,4),(16,4),(13,6)])
            r(hair_dark,(10,8,11,12));r(hair_dark,(20,7,21,12))
        elif side:
            p(ink,[(9,6),(12,2),(18,2),(22,5),(23,9),(21,13),(18,15),(12,14),(9,11)])
            p(skin,[(12,6),(18,4),(21,6),(22,9),(20,10),(19,13),(15,14),(12,11)])
            p(skin_light,[(15,6),(19,5),(20,7),(17,7)])
            p(hair,[(9,9),(10,4),(14,1),(19,2),(22,5),(20,7),(17,5),(13,6),(12,11)])
            p(hair_light,[(12,4),(15,2),(19,3),(16,4)])
            r(ink,(19,8,20,8));r(skin_shadow,(22,9,23,10))
            if obi:
                p(hair,[(14,11),(18,12),(21,10),(20,14),(17,16),(13,14)])
                l(hair_light,14,13,18,14)
            else:
                l(skin_shadow,20,8,19,11);r(hair_dark,(11,10,12,13))
        else:
            p(ink,[(9,6),(11,2),(16,1),(21,3),(23,7),(22,13),(19,16),(13,16),(9,12)])
            p(skin,[(11,6),(16,4),(21,6),(21,11),(18,14),(14,14),(11,11)])
            p(skin_light,[(13,6),(17,4),(20,6),(18,8),(14,8)])
            p(hair,[(9,10),(9,5),(13,1),(19,2),(23,5),(22,8),(19,6),(16,5),(13,7),(11,7),(11,12)])
            p(hair_light,[(12,4),(15,2),(19,3),(17,5),(13,6)])
            r(ink,(13,9,14,9));r(ink,(18,9,19,9));r(skin_shadow,(16,10,16,12))
            if obi:
                p(hair,[(11,11),(14,13),(17,12),(21,10),(20,14),(17,16),(13,15),(11,13)])
                l(hair_light,13,13,16,14,19,12)
            else:
                l(skin_shadow,20,8,20,11);l(hair_dark,10,9,11,13);l(hair_dark,19,5,21,7)
                r(skin_shadow,(14,13,18,13))
    if c[5]=='besalisk':r(7,(8,25,10,26));r(7,(23,25,26,26))
    if direction==3:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def font(size):
    for path in ('/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default()


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    if sys.argv[1:]==['--players-only']:
        for c in ROSTER:
            if c[0] not in ('Anakin Skywalker','Obi-Wan Kenobi'):continue
            name=slug(c[0]);path=ROOT/f'{name}.json';data=json.loads(path.read_text())
            frames=[overworld(c,r,k) for r in range(4) for k in range(4)]
            data['artRevision']=3;data['frames']=[encode(frame) for frame in frames]
            path.write_text(json.dumps(data,separators=(',',':'))+'\n')
            sheet=Image.new('RGBA',(128,128))
            for i,frame in enumerate(frames):sheet.paste(frame.convert('RGBA'),((i%4)*32,(i//4)*32))
            sheet.resize((512,512),Image.Resampling.NEAREST).save(ROOT/f'{name}-walk.png')
        print('Built the approved Anakin and Obi-Wan overworld revisions.')
        return
    board=Image.new('RGB',(1500,((len(ROSTER)+5)//6)*265+70),'#10171e');d=ImageDraw.Draw(board)
    d.text((25,20),'SOUL LINK · CLONE WARS · PIXELSTIL 02',font=font(25),fill='#ecd7ab')
    for index,c in enumerate(ROSTER):
        front=[battle(c,False,p) for p in range(2)];back=[battle(c,True,p) for p in range(2)]
        frames=[overworld(c,r,k) for r in range(4) for k in range(4)]
        pal=palette_of(front[0]);name=slug(c[0])
        # All images share one palette. Transparent border protects picture cipher.
        for im in front+back+frames:
            assert im.getpixel((im.width-1,im.height-1))==0
            assert len(im.getcolors())<=16
        data={'format':2,'artRevision':3 if c[0] in ('Anakin Skywalker','Obi-Wan Kenobi') else 2,'name':c[0],'size':32,
              'bladeIndices':[14,15] if c[5]=='yoda' else [13,14],
              'palette':[[round(v*31/255) for v in rgb] for rgb in pal],
              'frames':[encode(f) for f in frames],'front':[encode(f) for f in front],'back':[encode(f) for f in back]}
        (ROOT/f'{name}.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
        front[0].convert('RGBA').resize((320,320),Image.Resampling.NEAREST).save(ROOT/f'{name}-battle.png')
        sheet=Image.new('RGBA',(128,128))
        for i,im in enumerate(frames):sheet.paste(im.convert('RGBA'),((i%4)*32,(i//4)*32))
        sheet.resize((512,512),Image.Resampling.NEAREST).save(ROOT/f'{name}-walk.png')
        x=(index%6)*250;y=(index//6)*265+65
        d.rounded_rectangle((x+8,y,x+242,y+255),radius=12,fill='#1b252f')
        sprite=front[0].convert('RGBA').resize((200,200),Image.Resampling.NEAREST);board.paste(sprite,(x+24,y+5),sprite)
        field=frames[4].convert('RGBA');board.paste(field,(x+204,y+172),field)
        d.text((x+17,y+221),c[0],font=font(16),fill='#eee7d9')
    board.save(ROOT/'jedi-roster.png')
    print(f'Built {len(ROSTER)} approved-style character sets (front/back and 16 field frames).')


if __name__=='__main__':main()
