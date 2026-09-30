package soullink;

import com.dabomstew.pkrandom.pokemon.Pokemon;
import com.dabomstew.pkrandom.pokemon.Move;
import com.dabomstew.pkrandom.pokemon.MoveLearnt;
import com.dabomstew.pkrandom.pokemon.Encounter;
import com.dabomstew.pkrandom.pokemon.EncounterSet;
import com.dabomstew.pkrandom.pokemon.Trainer;
import com.dabomstew.pkrandom.pokemon.TrainerPokemon;
import com.dabomstew.pkrandom.pokemon.ExpCurve;
import com.dabomstew.pkrandom.Settings;
import com.dabomstew.pkrandom.Randomizer;
import com.dabomstew.pkrandom.romhandlers.Gen4RomHandler;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.ResourceBundle;

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
        StringBuilder json = new StringBuilder("{\"format\":2,\"moves\":{");
        boolean first = true;
        for (Move move : handler.getMoves()) {
            if (move == null || move.number <= 0 || move.number > 1000) continue;
            if (!first) json.append(',');
            first = false;
            json.append('"').append(move.number).append("\":{\"name\":")
                .append(jsonString(move.name)).append(",\"type\":")
                .append(jsonString(move.type == null ? "UNKNOWN" : move.type.name())).append(",\"category\":")
                .append(jsonString(move.category == null ? "STATUS" : move.category.name()))
                .append(",\"power\":").append(Math.max(0, move.power))
                .append(",\"pp\":").append(Math.max(0, move.pp)).append('}');
        }
        json.append("},\"pokemon\":[");
        Map<Integer,List<MoveLearnt>> movesLearnt = handler.getMovesLearnt();
        first = true;
        for (Pokemon pokemon : handler.getPokemon()) {
            if (pokemon == null || pokemon.number <= 0 || pokemon.number > 493) continue;
            if (!first) json.append(',');
            first = false;
            json.append("{\"species\":").append(pokemon.number).append(",\"name\":")
                .append(jsonString(pokemon.name))
                .append(",\"baseStats\":[").append(pokemon.hp).append(',').append(pokemon.attack)
                .append(',').append(pokemon.defense).append(',').append(pokemon.speed)
                .append(',').append(pokemon.spatk).append(',').append(pokemon.spdef).append(']')
                .append(",\"abilities\":[").append(pokemon.ability1).append(',').append(pokemon.ability2).append(']')
                .append(",\"genderRatio\":").append(pokemon.genderRatio)
                .append(",\"growth\":").append(pokemon.growthCurve.toByte())
                .append(",\"learnset\":[");
            boolean firstMove = true;
            for (MoveLearnt learnt : movesLearnt.getOrDefault(pokemon.number, List.of())) {
                if (!firstMove) json.append(',');
                firstMove = false;
                json.append('[').append(learnt.level).append(',').append(learnt.move).append(']');
            }
            json.append("]}");
        }
        json.append("]}\n");
        Files.createDirectories(destination.toAbsolutePath().normalize().getParent());
        Path temporary = destination.resolveSibling(destination.getFileName() + ".tmp");
        Files.writeString(temporary, json.toString(), StandardCharsets.UTF_8);
        try {
            Files.move(temporary, destination, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
            Files.move(temporary, destination, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static String encounterFingerprint(Gen4RomHandler handler) {
        StringBuilder value = new StringBuilder();
        for (EncounterSet set : handler.getEncounters(true)) {
            value.append('[').append(set.rate).append(':');
            for (Encounter encounter : set.encounters) {
                value.append(encounter.pokemon.number).append('/')
                    .append(encounter.formeNumber).append('/')
                    .append(encounter.level).append('/')
                    .append(encounter.maxLevel).append(',');
            }
            value.append(']');
        }
        return value.toString();
    }

    private static String trainerFingerprint(Gen4RomHandler handler) {
        StringBuilder value = new StringBuilder();
        for (Trainer trainer : handler.getTrainers()) {
            // rivalCarriesStarter deliberately changes the rival after selection;
            // every other trainer must remain byte-for-byte equivalent in meaning.
            if (trainer.forceStarterPosition >= 0 || (trainer.tag != null && trainer.tag.contains("RIVAL"))) continue;
            value.append('[').append(trainer.index).append(':');
            for (TrainerPokemon pokemon : trainer.pokemon) {
                value.append(pokemon.pokemon.number).append('/')
                    .append(pokemon.forme).append('/')
                    .append(pokemon.level).append('/')
                    .append(pokemon.heldItem).append(',');
            }
            value.append(']');
        }
        return value.toString();
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
            List<Pokemon> previous = new ArrayList<>(handler.getStarters());
            Pokemon chosen = handler.getPokemon().stream().filter(p -> p != null && p.number == species).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Dieses Pokémon ist in SoulSilver nicht verfügbar."));
            List<Pokemon> sides = new ArrayList<>();
            for (Pokemon pokemon : previous)
                if (pokemon.number != chosen.number && sides.stream().noneMatch(p -> p.number == pokemon.number)) sides.add(pokemon);
            for (Pokemon pokemon : handler.getPokemon()) {
                if (sides.size() >= 2) break;
                if (pokemon != null && pokemon.number > 0 && pokemon.number <= 493 && pokemon.number != chosen.number
                        && sides.stream().noneMatch(p -> p.number == pokemon.number)) sides.add(pokemon);
            }
            if (sides.size() < 2) throw new IllegalStateException("Zwei verschiedene Gegenstarter konnten nicht erhalten werden.");
            String encountersBefore = encounterFingerprint(handler);
            String trainersBefore = trainerFingerprint(handler);
            if (!handler.setStarters(List.of(sides.get(0), chosen, sides.get(1))))
                throw new IllegalStateException("Die Starterwahl konnte nicht festgelegt werden.");
            handler.rivalCarriesStarter();
            if (!handler.saveRomFile(output.toString(), 0)) throw new IllegalStateException("Die gewählte Starter-ROM konnte nicht gespeichert werden.");
            Gen4RomHandler verify = new Gen4RomHandler(new Random(0), System.out);
            if (!verify.loadRom(output.toString()) || verify.getStarters().size() != 3
                    || verify.getStarters().get(1).number != species
                    || verify.getStarters().stream().map(p -> p.number).distinct().count() != 3)
                throw new IllegalStateException("Die Starterwahl konnte nicht geprüft werden.");
            if (!encountersBefore.equals(encounterFingerprint(verify)) || !trainersBefore.equals(trainerFingerprint(verify)))
                throw new IllegalStateException("Die Auswahl hätte wilde Pokémon oder Trainer zurückgesetzt und wurde deshalb abgebrochen.");
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
        String originalEncounters = encounterFingerprint(handler);
        String originalTrainers = trainerFingerprint(handler);

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
        Settings settings = new Settings();
        settings.setRomName(handler.getROMName());
        settings.setSelectedEXPCurve(ExpCurve.MEDIUM_FAST);
        boolean adventure = args.length >= 4 && args[3].equals("adventure");
        if (adventure) {
            settings.setWildPokemonMod(false, true, false, false);
            settings.setBlockWildLegendaries(false);
            settings.setUseTimeBasedEncounters(true);
            settings.setTrainersMod(false, true, false, false, false, false);
            settings.setTrainersBlockLegendaries(true);
            settings.setTrainersBlockEarlyWonderGuard(true);
            settings.setRivalCarriesStarterThroughout(true);
            // Use UPR-ZX's complete, supported write pipeline. Calling only its
            // low-level mutation methods changed the in-memory tables but did
            // not persist those tables to the final DS image.
            ResourceBundle bundle = ResourceBundle.getBundle("com.dabomstew.pkrandom.newgui.Bundle");
            new Randomizer(settings, handler, bundle, false).randomize(output.toString(), System.out, seed);
        } else {
            handler.rivalCarriesStarter();
            if (!handler.saveRomFile(output.toString(), seed))
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
        if (adventure) {
            boolean wildSaved = !originalEncounters.equals(encounterFingerprint(verify));
            boolean trainersSaved = !originalTrainers.equals(trainerFingerprint(verify));
            if (!wildSaved || !trainersSaved)
                throw new IllegalStateException("Die gespeicherte ROM enthält keine vollständige Abenteuer-Randomisierung"
                    + " (wild=" + wildSaved + ", trainer=" + trainersSaved + ").");
        }
        if (args.length == 5) writeBattleData(verify, Path.of(args[4]).toAbsolutePath().normalize());

        System.out.printf("SOULLINK_STARTERS=%d:%s,%d:%s,%d:%s%n",
                starters.get(0).number, starters.get(0).name,
                starters.get(1).number, starters.get(1).name,
                starters.get(2).number, starters.get(2).name);
    }
}
