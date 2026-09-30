The release build includes two user-created SoulSilver checkpoint saves here:

- `Optimus.sav` — male trainer named Optimus
- `Bee.sav` — male trainer named Bee

Both saves stop immediately before the starter choice and are used only until a
launcher starter is selected. `poststarter-template.sav.gz` is a sanitized
checkpoint generated from the user-confirmed regular cloud save at 00:58:01.
The older v0.15.3 template only captured the last in-game save embedded in the
melonDS state, not its later running-memory position. This template contains
neither the original `.mln` file nor its original trainer/Pokémon identity. At
selection time the app creates a normal `.sav`, changes the trainer to Anakin or
Obi-Wan, and rebuilds T1 for the selected species. No ROM or emulator savestate
is stored here.
