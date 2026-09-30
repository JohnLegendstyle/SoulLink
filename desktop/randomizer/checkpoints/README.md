The release build includes two user-created SoulSilver checkpoint saves here:

- `Optimus.sav` — male trainer named Optimus
- `Bee.sav` — male trainer named Bee

Both saves stop immediately before the starter choice and are used only until a
launcher starter is selected. `poststarter-template.sav.gz` is a sanitized
checkpoint generated from the user-provided melonDS example state. It contains
neither the original `.mln` file nor its original trainer/Pokémon identity. At
selection time the app creates a normal `.sav`, changes the trainer to Anakin or
Obi-Wan, and rebuilds T1 for the selected species. No ROM or emulator savestate
is stored here.
