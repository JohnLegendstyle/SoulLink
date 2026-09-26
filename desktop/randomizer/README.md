# Starter randomizer adapter

This source file uses the GPL-3.0 Universal Pokemon Randomizer ZX API. Build it
against `PokeRandoZX.jar` and include both the resulting class and the upstream
jar in desktop release packages. ROM files and save files are deliberately not
part of the repository or release packages.

```sh
javac -cp PokeRandoZX.jar -d classes StarterRandomizer.java
java -cp "classes:PokeRandoZX.jar" soullink.StarterRandomizer input.nds output.nds 12345
```

On Windows, use `;` instead of `:` in the Java classpath.
