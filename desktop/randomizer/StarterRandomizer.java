package soullink;

import com.dabomstew.pkrandom.pokemon.Pokemon;
import com.dabomstew.pkrandom.pokemon.Move;
import com.dabomstew.pkrandom.Settings;
import com.dabomstew.pkrandom.romhandlers.Gen4RomHandler;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Small GPL-compatible adapter around Universal Pokemon Randomizer ZX.
 * It guarantees at least one legendary starter and optionally randomizes
 * wild encounters and trainer teams. The original ROM is never modified.
 */
public final class StarterRandomizer {
    private StarterRandomizer() {}

    private static String jsonString(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c == '\\' || c == '"') out.append('\\').append(c);
            else if (c == '\n') out.append("\\n");
            else if (c == '\r') out.append("\\r");
            else if (c == '\t') out.append("\\t");
            else if (c < 32) out.append(String.format("\\u%04x", (int)c));
            else out.append(c);
        }
        return out.append('"').toString();
    }

    private static void writeBattleData(Gen4RomHandler handler, Path destination) throws Exception {
        StringBuilder json = new StringBuilder("{\"format\":1,\"moves\":{");
        boolean first = true;
        for (Move move : handler.getMoves()) {
            if (move == null || move.number <= 0 || move.number > 1000 || move.type == null) continue;
            if (!first) json.append(',');
            first = false;
            json.append('"').append(move.number).append("\":{\"name\":")
                .append(jsonString(move.name)).append(",\"type\":")
                .append(jsonString(move.type.name())).append(",\"category\":")
                .append(jsonString(move.category == null ? "STATUS" : move.category.name()))
                .append(",\"power\":").append(Math.max(0, move.power)).append('}');
        }
        json.append("}}\n");
        Files.createDirectories(destination.toAbsolutePath().normalize().getParent());
        Path temporary = destination.resolveSibling(destination.getFileName() + ".tmp");
        Files.writeString(temporary, json.toString(), StandardCharsets.UTF_8);
        try {
            Files.move(temporary, destination, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
            Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 3 && args[0].equals("--describe")) {
            Path input = Path.of(args[1]).toAbsolutePath().normalize();
            Path metadata = Path.of(args[2]).toAbsolutePath().normalize();
            Gen4RomHandler handler = new Gen4RomHandler(new Random(0), System.out);
            if (!handler.loadRom(input.toString())) throw new IllegalArgumentException("Diese ROM wird nicht als Pokémon HeartGold/SoulSilver erkannt.");
            writeBattleData(handler, metadata);
            return;
        }
        if (args.length == 4 && args[0].equals("--select")) {
            Path input = Path.of(args[1]).toAbsolutePath().normalize();
            Path output = Path.of(args[2]).toAbsolutePath().normalize();
            int species = Integer.parseInt(args[3]);
            Gen4RomHandler handler = new Gen4RomHandler(new Random(0), System.out);
            if (!handler.loadRom(input.toString())) throw new IllegalArgumentException("Diese ROM wird nicht als Pokémon HeartGold/SoulSilver erkannt.");
            Pokemon chosen = handler.getStarters().stream().filter(p -> p.number == species).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Dieses Pokémon gehört nicht zu den drei Startern dieser Runde."));
            if (!handler.setStarters(List.of(chosen, chosen, chosen))) throw new IllegalStateException("Die Starterwahl konnte nicht festgelegt werden.");
            handler.rivalCarriesStarter();
            if (!handler.saveRomFile(output.toString(), 0)) throw new IllegalStateException("Die gewählte Starter-ROM konnte nicht gespeichert werden.");
            Gen4RomHandler verify = new Gen4RomHandler(new Random(0), System.out);
            if (!verify.loadRom(output.toString()) || verify.getStarters().stream().anyMatch(p -> p.number != species))
                throw new IllegalStateException("Die Starterwahl konnte nicht geprüft werden.");
            return;
        }
        if (args.length < 3 || args.length > 5) {
            System.err.println("Usage: StarterRandomizer <input.nds> <output.nds> <seed> [mode] [battle-data.json]");
            System.exit(2);
        }

        Path input = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[1]).toAbsolutePath().normalize();
        long seed = Long.parseUnsignedLong(args[2]);
        if (!Files.isRegularFile(input)) {
            throw new IllegalArgumentException("Die Eingabe-ROM wurde nicht gefunden: " + input);
        }
        if (input.equals(output)) {
            throw new IllegalArgumentException("Die Original-ROM darf nicht überschrieben werden.");
        }
        Files.createDirectories(output.getParent());

        Random random = new Random(seed);
        Gen4RomHandler handler = new Gen4RomHandler(random, System.out);
        if (!handler.loadRom(input.toString())) {
            throw new IllegalArgumentException("Diese ROM wird nicht als Pokémon HeartGold/SoulSilver erkannt.");
        }

        List<Pokemon> all = new ArrayList<>();
        List<Pokemon> legendary = new ArrayList<>();
        for (Pokemon pokemon : handler.getPokemon()) {
            if (pokemon == null || pokemon.number <= 0 || pokemon.number > 493) continue;
            all.add(pokemon);
            if (pokemon.isLegendary()) legendary.add(pokemon);
        }
        if (legendary.isEmpty()) throw new IllegalStateException("Keine legendären Pokémon gefunden.");

        Collections.shuffle(all, random);
        Pokemon guaranteedLegendary = legendary.get(random.nextInt(legendary.size()));
        List<Pokemon> starters = new ArrayList<>(List.of(guaranteedLegendary));
        for (Pokemon pokemon : all) {
            if (starters.stream().noneMatch(p -> p.number == pokemon.number)) starters.add(pokemon);
            if (starters.size() == 3) break;
        }
        Collections.shuffle(starters, random);

        if (!handler.setStarters(starters)) {
            throw new IllegalStateException("Die Starter konnten in dieser ROM nicht geändert werden.");
        }
        // Optional full adventure mode preserves levels, species stats and moves.
        // Main-story gifts/static encounters stay unchanged to preserve scripts.
        Settings settings = new Settings();
        handler.setPokemonPool(settings);
        if (args.length == 4 && args[3].equals("adventure")) {
            settings.setWildPokemonMod(false, true, false, false);
            settings.setBlockWildLegendaries(false);
            settings.setUseTimeBasedEncounters(true);
            settings.setTrainersMod(false, true, false, false, false, false);
            settings.setTrainersBlockLegendaries(true);
            settings.setTrainersBlockEarlyWonderGuard(true);
            handler.randomEncounters(settings);
            handler.randomizeTrainerPokes(settings);
        }
        handler.rivalCarriesStarter();
        if (!handler.saveRomFile(output.toString(), seed)) {
            throw new IllegalStateException("Die randomisierte ROM konnte nicht gespeichert werden.");
        }
        Gen4RomHandler verify = new Gen4RomHandler(new Random(seed), System.out);
        if (!verify.loadRom(output.toString())) throw new IllegalStateException("Ausgabe-ROM konnte nicht erneut geladen werden.");
        List<Pokemon> actual = verify.getStarters();
        if (actual.size() != 3 || actual.stream().noneMatch(Pokemon::isLegendary)
                || actual.stream().map(p -> p.number).distinct().count() != 3) {
            throw new IllegalStateException("Starterprüfung der geschriebenen ROM fehlgeschlagen.");
        }
        for (int i=0;i<3;i++) if (actual.get(i).number != starters.get(i).number)
            throw new IllegalStateException("Gespeicherte Starter unterscheiden sich von der Auswahl.");
        if (args.length == 5) writeBattleData(verify, Path.of(args[4]).toAbsolutePath().normalize());

        System.out.printf("SOULLINK_STARTERS=%d:%s,%d:%s,%d:%s%n",
                starters.get(0).number, starters.get(0).name,
                starters.get(1).number, starters.get(1).name,
                starters.get(2).number, starters.get(2).name);
    }
}
