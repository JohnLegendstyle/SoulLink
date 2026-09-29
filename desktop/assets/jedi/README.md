# Clone Wars pixel-art pack

Unofficial fan art. Characters belong to Lucasfilm. No Nintendo graphics or
downloaded Star Wars artwork are distributed in this folder. Most designs are
drawn by the versioned coordinate sources `desktop/tools/draw_jedi_v2.py` and
`desktop/tools/jedi_approved.py` using Pillow as a local rasterizer. Revision 4
uses the locally stored generated concept
`anakin-obiwan-overworld-source.png` for the two player field sprites and maps
it deterministically into the shared native 16-color ROM palettes. Playing and
building the packaged app requires no model, network service or API key.

45 Jedi/Padawan designs are in `roster.json`, including Anakin and Obi-Wan.
This is the implemented roster, not a claim of covering every unnamed or cameo
Jedi in the series. See `jedi-roster.png` for all designs before applying.
Each has 16 native 32x32 walking frames, two 80x80 battle-front poses and two
battle-back poses. Limited 16-entry RGB555 palettes include transparency and a
visible lightsaber. JSON files are runtime assets; PNGs are development previews.

John: Anakin Skywalker; Eddie: Obi-Wan Kenobi. Both use blue lightsabers.
Game trainer names are Anakin and Obi-Wan. Legacy internal round keys remain
Optimus/Bee to preserve existing paths and account pairings.

The patch changes only the graphics archives a/0/8/1, a/0/5/8 and a/0/0/6 in the
user's own German SoulSilver ROM. 129 battle-front trainer classes and 17 back
sets are replaced. Supported walking/running field sheets are replaced; action
sheets such as bicycle/surf/fishing and trainer-card illustrations are not.
Generic field sprites may also be used by civilians. Dialogs, opponent names,
trainer parties, encounter tables and game logic are not edited.

Existing ROMs are backed up as `.pre-jedi.nds`; pre-starter name migration backs
up `.pre-jedi-name.sav`. Changing a legacy name after Pokémon were acquired is
deliberately blocked until original-trainer ownership migration is implemented.
Graphics-only changes retain the previous cloud identity via a hash-checked
`.graphics-identity.json` sidecar. Copy the whole round including sidecars, and
use app 0.8 or later on every device. No cloud history is discarded.

Technical references (data-layout facts, no game pixels copied):
- https://github.com/pret/pokeheartgold/blob/master/src/pokepic.c
- https://github.com/pret/pokeheartgold/blob/master/include/constants/trainer_class.h
- https://github.com/pret/pokeheartgold/blob/master/lib/include/nnsys/g2d/fmt/g2d_Cell_data.h
- https://www.starwars.com/databank/the-clone-wars-all

Revision 2 adopts the approved Plo Koon/Yoda pixel language for all 45 designs.
Their first front frames remain pixel-identical to the approved native drawings.
Every character includes explicit palette indices for its two blade colors;
palette index meanings are not assumed to be identical between alien designs.

Revision 4 replaces the small Anakin/Obi-Wan field sprites with the approved
slimmer Clone-Wars proportions, directional hair/beard/costume silhouettes and
lightsabers held close to the body.

Rebuild: `python desktop/tools/draw_jedi_v2.py` (development Pillow installation).
`draw_jedi.py` retains the roster and legacy source for comparison only.
