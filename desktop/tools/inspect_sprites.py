"""Development-only contact sheets extracted from the user's own ROM."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw
from ndspy.rom import NintendoDSRom
from ndspy.narc import NARC
from ndspy.texture import NSBTX
import ndspy.color
ndspy.color.prepareLUTs()

rom=NintendoDSRom.fromFile(sys.argv[1])
archive=NARC(rom.getFileByName('a/0/8/1'))
output=Path(sys.argv[2]); output.mkdir(parents=True,exist_ok=True)
for index in map(int,sys.argv[3:]):
    btx=NSBTX(archive.files[index])
    btx.palettes[0][1].colors=[c.r|(c.g<<5)|(c.b<<10) for c in btx.palettes[0][1].colors]
    frames=sorted(btx.textures,key=lambda p:int(p[0].rsplit('.',1)[-1]))
    canvas=Image.new('RGB',(8*128,((len(frames)+7)//8)*150),'#d2d8df')
    draw=ImageDraw.Draw(canvas)
    for i,(name,texture) in enumerate(frames):
        im=texture.renderAsImage(btx.palettes[0][1])
        x,y=(i%8)*128,(i//8)*150
        im=im.resize((texture.width*3,texture.height*3),Image.Resampling.NEAREST)
        canvas.paste(im,(x,y+20),im)
        draw.text((x+2,y+2),name,fill='black')
    canvas.save(output/f'overworld-{index}.png')
    print(index,len(frames),{t.size for _,t in frames},[p[0] for p in btx.palettes])
