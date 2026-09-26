from __future__ import annotations

import json
import os
import platform
import threading
import queue
import subprocess
import webbrowser
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .melonds import DEFAULT_KEYS, copy_emulator, find_executable, launch, write_config, qt_key, read_runtime_settings
from .randomizer import PlayerPack, create_round, runtime_root, load_round, install_root
from .sync import SyncWorker


COLORS = {
    "bg": "#101214", "panel": "#191c1f", "panel2": "#25292d",
    "line": "#3a4046", "text": "#eceff1", "muted": "#9ca2a7",
    "blue": "#e7b85d", "gold": "#e7b85d", "green": "#b5c7b0",
}


def config_root() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "SoulLink"


class SoulLinkApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Soul Link · Focus · {__version__}")
        self.geometry("980x800")
        self.minsize(920, 760)
        self.configure(bg=COLORS["bg"])
        self.state_file = config_root() / "config.json"
        self.settings = self._load()
        self.packs: dict[str, PlayerPack] = {}
        self.sync_worker: SyncWorker | None = None
        self.processes = {}
        self.runtime = {}
        self.creating = False
        self.events = queue.Queue()
        self._style()
        self._menu()
        self._layout()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.drain_events)
        previous = self.settings.get('manifest')
        if previous:
            try:
                self.packs = {p.player:p for p in load_round(Path(str(previous)))}
                self.status_var.set('Letzte Runde geladen. Ihr könnt weiterspielen.')
            except (OSError, ValueError, KeyError):
                self.status_var.set('Letzte Runde nicht gefunden. Bitte vorhandene Runde öffnen.')

    def _load(self) -> dict[str, object]:
        defaults: dict[str, object] = {
            "rom": "", "emulator": "", "output": str(Path.home() / "Downloads" / "SoulLink-Runden"),
            "scale": 4, "fps": 60, "volume": 80, "fullscreen": True, "player": "Optimus",
            "keys": dict(DEFAULT_KEYS), "connection": "", "save": "",
            "adventure": True, "pixel_filter": False, "integer_scaling": False, "screen_layout": "focus",
        }
        try:
            loaded = json.loads(self.state_file.read_text(encoding="utf-8"))
            defaults.update(loaded)
        except (OSError, ValueError):
            pass
        if not defaults['emulator']:
            bundled = install_root() / 'Emulator' / ('melonDS.app' if platform.system() == 'Darwin' else 'melonDS.exe')
            if bundled.exists(): defaults['emulator'] = str(bundled)
        return defaults

    def _save(self) -> None:
        self.settings.update({
            "rom": self.rom_var.get(), "emulator": self.emu_var.get(), "output": self.output_var.get(),
            "scale": int(self.scale_var.get()), "fps": int(self.fps_var.get()),
            "volume": int(self.volume_var.get()), "fullscreen": bool(self.fullscreen_var.get()), "player": self.player_var.get(),
            "connection": self.connection_var.get(), "save": self.save_var.get(),
            "keys": {name: var.get() for name, var in self.key_vars.items()},
            "adventure": bool(self.adventure_var.get()),
            "pixel_filter": self.filter_var.get() == 'Weich',
            "integer_scaling": bool(self.integer_var.get()),
            "screen_layout": {'Focus':'focus','Nebeneinander':'horizontal','Untereinander':'vertical'}[self.layout_var.get()],
        })
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.settings, indent=2, ensure_ascii=False), encoding="utf-8")
        if os.name != 'nt': self.state_file.chmod(0o600)

    def _style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Arial", 12))
        style.configure("Title.TLabel", font=("Arial", 28, "bold"), foreground=COLORS["text"])
        style.configure("Sub.TLabel", foreground=COLORS["muted"], font=("Arial", 11))
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("TButton", padding=(14, 9), font=("Arial", 11, "bold"), background=COLORS["panel2"], foreground=COLORS["text"],borderwidth=0,relief='flat',bordercolor=COLORS['panel2'],lightcolor=COLORS['panel2'],darkcolor=COLORS['panel2'])
        style.map("TButton", background=[("active", "#24405f")])
        style.configure("Primary.TButton", background=COLORS["blue"], foreground="#10213b")
        style.map("Primary.TButton", background=[("active", "#f1cc83")])
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0,bordercolor=COLORS['bg'],lightcolor=COLORS['bg'],darkcolor=COLORS['bg'])
        style.configure("TNotebook.Tab", background=COLORS["panel"], foreground=COLORS["muted"], padding=(18, 10),borderwidth=0,bordercolor=COLORS['panel'],lightcolor=COLORS['panel'],darkcolor=COLORS['panel'])
        style.map("TNotebook.Tab", background=[("selected", COLORS["panel2"])], foreground=[("selected", COLORS["text"])])
        style.configure("TEntry", fieldbackground="#0f1724", foreground=COLORS["text"], insertcolor=COLORS["text"], padding=7,bordercolor=COLORS['line'],lightcolor=COLORS['line'],darkcolor=COLORS['line'])
        style.configure("TCombobox", fieldbackground="#0f1724", foreground=COLORS["text"], padding=7,bordercolor=COLORS['line'],lightcolor=COLORS['line'],darkcolor=COLORS['line'],arrowcolor=COLORS['blue'])
        style.map('TCombobox',fieldbackground=[('readonly','#0f1724')],foreground=[('readonly',COLORS['text'])])
        style.configure("Horizontal.TScale", background=COLORS["panel"])
        style.configure("TCheckbutton", background=COLORS['panel'], foreground=COLORS['text'], font=('Arial',11))

    def _menu(self) -> None:
        menu = tk.Menu(self)
        game = tk.Menu(menu, tearoff=False)
        game.add_command(label="Neue randomisierte Runde", command=self.create_new_round)
        game.add_command(label="Vorhandene Runde öffnen", command=self.open_round)
        game.add_command(label="Optimus Prime & Bumblebee anwenden", command=self.apply_character_skins)
        game.add_separator()
        game.add_command(label="Optimus starten", command=lambda: self.start_player("Optimus"))
        game.add_command(label="Bee starten", command=lambda: self.start_player("Bee"))
        game.add_separator()
        game.add_command(label="Beenden", command=self.close)
        menu.add_cascade(label="Spiel", menu=game)
        menu.add_command(label="Emulator-Einstellungen", command=lambda: self.tabs.select(self.settings_tab))
        self.config(menu=menu)

    def _layout(self) -> None:
        top = ttk.Frame(self, padding=(30, 24, 30, 12))
        top.pack(fill="x")
        ttk.Label(top, text="SOUL LINK  /  FOCUS", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Dein Spiel im Mittelpunkt. Optimus × Bee · Windows + macOS", style="Sub.TLabel").pack(anchor="w", pady=(3, 0))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=30, pady=(4, 22))
        self.round_tab = ttk.Frame(self.tabs, padding=22, style="Panel.TFrame")
        self.settings_tab = ttk.Frame(self.tabs, padding=22, style="Panel.TFrame")
        self.sync_tab = ttk.Frame(self.tabs, padding=22, style="Panel.TFrame")
        self.tabs.add(self.round_tab, text="Spielen & Runden")
        self.tabs.add(self.settings_tab, text="Grafik · Sound · Tasten")
        self.tabs.add(self.sync_tab, text="Gemeinsamer Tracker")
        self._round_ui()
        self._settings_ui()
        self._sync_ui()

    def _field(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, browse) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        ttk.Button(parent, text="Auswählen", command=browse).grid(row=row, column=2, pady=8)

    def _round_ui(self) -> None:
        tab = self.round_tab
        tab.columnconfigure(1, weight=1)
        ttk.Label(tab, text="Mit einem Klick zwei neue Spiele", style="Panel.TLabel", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(tab, text="Jede Seite bekommt drei neue Starter. Mindestens einer davon ist legendär.", style="Panel.TLabel", foreground=COLORS["muted"]).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 15))
        self.rom_var = tk.StringVar(value=str(self.settings["rom"]))
        self.emu_var = tk.StringVar(value=str(self.settings["emulator"]))
        self.output_var = tk.StringVar(value=str(self.settings["output"]))
        self._field(tab, 2, "Originale SoulSilver-ROM", self.rom_var, self.pick_rom)
        self._field(tab, 3, "melonDS", self.emu_var, self.pick_emulator)
        self._field(tab, 4, "Runden-Ordner", self.output_var, self.pick_output)
        self.adventure_var = tk.BooleanVar(value=bool(self.settings['adventure']))
        self.status_var = tk.StringVar(value="Bereit für eine neue Runde.")
        self.create_button = ttk.Button(tab, text="Neue randomisierte Runde erstellen", style="Primary.TButton", command=self.create_new_round)
        self.create_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(20, 12))
        ttk.Label(tab, textvariable=self.status_var, style="Panel.TLabel", foreground=COLORS["green"], wraplength=760).grid(row=6, column=0, columnspan=3, sticky="w", pady=6)
        actions = ttk.Frame(tab, style="Panel.TFrame")
        actions.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        actions.columnconfigure((0, 1), weight=1)
        ttk.Button(actions, text="Optimus starten", command=lambda: self.start_player("Optimus")).grid(row=0, column=0, sticky="ew", padx=(0, 7))
        ttk.Button(actions, text="Bee starten", command=lambda: self.start_player("Bee")).grid(row=0, column=1, sticky="ew", padx=(7, 0))
        ttk.Button(actions, text="Vorhandene Runde öffnen", command=self.open_round).grid(row=1,column=0,sticky='ew',pady=12,padx=(0,7))
        ttk.Button(actions, text="Runden-Ordner anzeigen", command=self.show_output).grid(row=1,column=1,sticky='ew',pady=12,padx=(7,0))
        ttk.Button(actions, text="Optimus Prime & Bumblebee · Figuren aktualisieren", command=self.apply_character_skins).grid(row=2,column=0,columnspan=2,sticky='ew')
        ttk.Label(tab,text='Neue Runden erhalten einen eigenen Ordner. Eure bisherigen Spielstände bleiben erhalten.\nDie Starter entdeckt ihr erst bei der Auswahl im Spiel.',style='Panel.TLabel',foreground=COLORS['muted']).grid(row=8,column=0,columnspan=3,sticky='w',pady=14)
        ttk.Checkbutton(tab,text='Auch wilde Pokémon und gegnerische Teams randomisieren',variable=self.adventure_var).grid(row=9,column=0,columnspan=3,sticky='w')

    def _settings_ui(self) -> None:
        tab = self.settings_tab
        tab.columnconfigure(1, weight=1)
        self.scale_var = tk.StringVar(value=str(self.settings["scale"]))
        self.fps_var = tk.StringVar(value=str(self.settings["fps"]))
        self.volume_var = tk.IntVar(value=int(self.settings["volume"]))
        self.fullscreen_var = tk.BooleanVar(value=bool(self.settings["fullscreen"]))
        ttk.Label(tab, text="Interne 3D-Auflösung", style="Panel.TLabel").grid(row=0, column=0, sticky="w", pady=7)
        ttk.Combobox(tab, textvariable=self.scale_var, state="readonly", values=("1", "2", "3", "4", "6", "8", "12", "16")).grid(row=0, column=1, sticky="ew", padx=12)
        ttk.Label(tab, text="FPS / Spieltempo", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=7)
        ttk.Combobox(tab, textvariable=self.fps_var, state="readonly", values=("60", "90", "120", "0")).grid(row=1, column=1, sticky="ew", padx=12)
        ttk.Label(tab, text="0 = unbegrenzt; 60 FPS ist normales Spieltempo.", style="Panel.TLabel", foreground=COLORS["muted"]).grid(row=2, column=1, sticky="w", padx=12)
        ttk.Label(tab, text="Lautstärke", style="Panel.TLabel").grid(row=3, column=0, sticky="w", pady=7)
        ttk.Scale(tab, from_=0, to=100, variable=self.volume_var).grid(row=3, column=1, sticky="ew", padx=12)
        ttk.Checkbutton(tab, text="Spiel direkt im Vollbild starten", variable=self.fullscreen_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 4))
        self.filter_var=tk.StringVar(value='Weich' if self.settings['pixel_filter'] else 'Scharf')
        self.integer_var=tk.BooleanVar(value=bool(self.settings['integer_scaling']))
        self.layout_var=tk.StringVar(value={'focus':'Focus','horizontal':'Nebeneinander','vertical':'Untereinander'}.get(str(self.settings['screen_layout']),'Focus'))
        display=ttk.Frame(tab,style='Panel.TFrame')
        display.grid(row=5,column=0,columnspan=2,sticky='ew',pady=(10,0))
        ttk.Label(display,text='Pixel-Skalierung',style='Panel.TLabel').pack(side='left')
        ttk.Combobox(display,textvariable=self.filter_var,state='readonly',values=('Scharf','Weich'),width=8).pack(side='left',padx=10)
        ttk.Combobox(display,textvariable=self.layout_var,state='readonly',values=('Focus','Nebeneinander','Untereinander'),width=16).pack(side='left',padx=10)
        ttk.Checkbutton(display,text='Ganzzahlige Skalierung',variable=self.integer_var).pack(side='left',padx=10)
        keys = dict(self.settings.get("keys", DEFAULT_KEYS))
        self.key_vars: dict[str, tk.StringVar] = {}
        labels = tuple((n,n) for n in ('A','B','X','Y','L','R','Start','Select','Up','Down','Left','Right')) + (("HK_FastForward", "Schnelllauf"),("HK_FullscreenToggle", "Vollbild"))
        box = ttk.Frame(tab, style="Panel.TFrame")
        box.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        for index, (name, label) in enumerate(labels):
            row, col = divmod(index, 3)
            frame = ttk.Frame(box, style="Panel.TFrame")
            frame.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
            box.columnconfigure(col, weight=1)
            ttk.Label(frame, text=label, style="Panel.TLabel").pack(side="left")
            var = tk.StringVar(value=str(keys.get(name, DEFAULT_KEYS[name])))
            self.key_vars[name] = var
            ttk.Entry(frame, textvariable=var, width=9).pack(side="right")
        ttk.Button(tab, text="Einstellungen speichern", style="Primary.TButton", command=self.save_emulator_settings).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(18, 0))

    def _sync_ui(self) -> None:
        tab = self.sync_tab
        tab.columnconfigure(1, weight=1)
        self.connection_var = tk.StringVar(value=str(self.settings["connection"]))
        self.save_var = tk.StringVar(value=str(self.settings["save"]))
        self.player_var = tk.StringVar(value=str(self.settings["player"]))
        self._field(tab, 0, "Verbindungsdatei", self.connection_var, lambda: self.connection_var.set(filedialog.askopenfilename(filetypes=[("Soul Link", "*.json")]) or self.connection_var.get()))
        self._field(tab, 1, "Spielstand", self.save_var, lambda: self.save_var.set(filedialog.askopenfilename(filetypes=[("Nintendo DS Save", "*.sav")]) or self.save_var.get()))
        ttk.Label(tab, text="Spieler", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Label(tab, text='Spieler wird aus der Verbindungsdatei erkannt.', style='Panel.TLabel').grid(row=2,column=1,sticky='w',padx=12)
        self.sync_status = tk.StringVar(value="Nicht verbunden")
        ttk.Button(tab, text="Spielstand-Synchronisierung starten", style="Primary.TButton", command=self.start_sync).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(22, 10))
        ttk.Button(tab, text="Verbindung stoppen", command=self.stop_sync).grid(row=4, column=0, columnspan=3, sticky="ew")
        ttk.Label(tab, textvariable=self.sync_status, style="Panel.TLabel", foreground=COLORS["green"], wraplength=760).grid(row=5, column=0, columnspan=3, sticky="w", pady=15)
        ttk.Label(tab,text='Der Tracker aktualisiert sich nach dem Speichern im Spiel. K. o. wird nur erkannt,\nwenn mit 0 KP gespeichert wurde. Partner-Sperren werden angezeigt;\ndie App entfernt keine Pokémon automatisch aus eurem Spiel.',style='Panel.TLabel',foreground=COLORS['muted']).grid(row=6,column=0,columnspan=3,sticky='w',pady=16)
        ttk.Button(tab,text='Gemeinsamen Tracker öffnen',command=lambda:webbrowser.open('https://soullink-web-production.up.railway.app')).grid(row=7,column=0,columnspan=3,sticky='ew')

    def pick_rom(self) -> None:
        value = filedialog.askopenfilename(filetypes=[("Nintendo DS ROM", "*.nds")])
        if value: self.rom_var.set(value)

    def pick_emulator(self) -> None:
        value = filedialog.askopenfilename(title="melonDS auswählen")
        if value: self.emu_var.set(value)

    def pick_output(self) -> None:
        value = filedialog.askdirectory(title="Runden-Ordner auswählen")
        if value: self.output_var.set(value)

    def create_new_round(self) -> None:
        if self.creating: return
        if any(p.poll() is None for p in self.processes.values()):
            messagebox.showinfo('Neue Runde','Bitte zuerst das laufende Spiel schließen.'); return
        try:
            self._save()
        except (OSError,ValueError) as error:
            messagebox.showerror('Einstellungen',str(error)); return
        source, destination = Path(self.rom_var.get()), Path(self.output_var.get())
        mode = 'adventure' if self.adventure_var.get() else 'starters'
        self.creating = True
        self.create_button.state(['disabled'])
        self.status_var.set("Die beiden ROMs werden randomisiert …")
        def work() -> None:
            try:
                round_dir, packs = create_round(source, destination, runtime_root() / "checkpoints", mode)
                self.events.put(('round', (round_dir, packs)))
            except Exception as error:
                self.events.put(('error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def save_emulator_settings(self) -> None:
        try:
            for v in self.key_vars.values(): qt_key(v.get())
            self._save()
            messagebox.showinfo("Einstellungen", "Gespeichert. Die Einstellungen gelten beim nächsten Spielstart.")
        except Exception as error:
            messagebox.showerror("Einstellungen", str(error))

    def apply_character_skins(self) -> None:
        if self.creating: return
        if not self.packs:
            messagebox.showinfo('Figuren','Bitte zuerst eure vorhandene Runde öffnen.'); return
        if any(p.poll() is None for p in self.processes.values()):
            messagebox.showinfo('Figuren','Bitte zuerst das laufende Spiel schließen.'); return
        if not messagebox.askokcancel('Optimus Prime & Bumblebee',
            'Bitte auch separat gestartete melonDS-Fenster schließen.\n\n'
            'Ersetzt die Lauf- und Rennfiguren in eurer aktuellen Runde. '
            'Spielstände und Pokémon bleiben unverändert. Die bisherigen ROMs werden gesichert.\n\n'
            'Kampfporträts und Spezialaktionen bleiben vorerst im Originaldesign.'):
            return
        from .skins import apply_skin
        packs = list(self.packs.values())
        self.creating = True
        self.create_button.state(['disabled'])
        self.status_var.set('Die Spielfiguren werden aktualisiert …')
        def work() -> None:
            try:
                for pack in packs: apply_skin(pack.rom,pack.player)
                self.events.put(('skins',None))
            except Exception as error:
                self.events.put(('error',str(error)))
        threading.Thread(target=work,daemon=True).start()

    def start_player(self, player: str) -> None:
        try:
            pack = self.packs.get(player)
            if self.creating: raise RuntimeError('Bitte warten, bis die Runde fertig ist.')
            if player in self.processes and self.processes[player].poll() is None:
                raise RuntimeError('Dieses Spiel läuft bereits.')
            if any(p.poll() is None for p in self.processes.values()):
                raise RuntimeError('Bitte das andere Spielfenster vor dem Spielerwechsel schließen.')
            if not pack:
                raise RuntimeError("Bitte zuerst eine neue randomisierte Runde erstellen.")
            self._save()
            source = Path(self.emu_var.get()).expanduser().resolve()
            find_executable(source)
            isolated = config_root() / 'Emulator' / player
            isolated.mkdir(parents=True,exist_ok=True)
            executable = copy_emulator(source,isolated)
            write_config(executable, scale=int(self.scale_var.get()), fps=int(self.fps_var.get()),
                         volume_percent=int(self.volume_var.get()),
                         keys={name: value.get() for name, value in self.key_vars.items()},
                         save_directory=pack.rom.parent,pixel_filter=self.filter_var.get()=='Weich',
                         integer_scaling=bool(self.integer_var.get()),screen_layout=str(self.settings['screen_layout']))
            request=config_root()/'requests'/(uuid.uuid4().hex+'.json')
            request.parent.mkdir(parents=True,exist_ok=True)
            self.processes[player] = launch(executable, pack.rom, fullscreen=bool(self.fullscreen_var.get()),player=player,request=request)
            self.runtime[player]=(executable,request)
            self.save_var.set(str(pack.save))
            self._save()
            self.withdraw()
        except Exception as error:
            messagebox.showerror("Spiel starten", str(error))

    def start_sync(self) -> None:
        try:
            self.stop_sync()
            self._save()
            self.sync_worker = SyncWorker(Path(self.connection_var.get()), Path(self.save_var.get()), lambda text: self.events.put(('sync',text)))
            self.sync_worker.start()
            self.sync_status.set("Verbindung wird aufgebaut …")
        except Exception as error:
            messagebox.showerror("Live-Verbindung", str(error))

    def drain_events(self) -> None:
        for player,(executable,request) in list(self.runtime.items()):
            process=self.processes[player]
            if process.poll() is None: continue
            del self.runtime[player]
            try:
                values=read_runtime_settings(executable)
                self.scale_var.set(str(values['scale']));self.fps_var.set(str(values['fps']));self.volume_var.set(values['volume'])
                self.filter_var.set('Weich' if values['pixel_filter'] else 'Scharf');self.integer_var.set(values['integer_scaling'])
                self.layout_var.set({'focus':'Focus','horizontal':'Nebeneinander','vertical':'Untereinander'}[values['screen_layout']])
                for key,value in values['keys'].items(): self.key_vars[key].set(value)
                self._save()
            except (OSError,ValueError,KeyError,TypeError):
                self.status_var.set('Emulator beendet. Letzte gültige Einstellungen bleiben erhalten.')
            self.deiconify();self.lift()
            if process.returncode:
                self.status_var.set('Das Spielfenster wurde unerwartet beendet. Euer gespeicherter Fortschritt bleibt erhalten.')
            try:
                action=json.loads(request.read_text()).get('action')
                request.unlink()
                if action=='new-round': self.after(200,self.create_new_round)
                elif action in ('start:Optimus','start:Bee'):
                    self.after(200,lambda p=action.split(':')[1]:self.start_player(p))
            except (OSError,ValueError,AttributeError): pass
        while not self.events.empty():
            kind,value = self.events.get_nowait()
            if kind in ('round','skins','error'):
                self.creating = False
                self.create_button.state(['!disabled'])
            if kind == 'round':
                directory,packs = value
                self.packs = {p.player:p for p in packs}
                self.settings['manifest'] = str(directory / 'runde.json')
                self._save()
                self.status_var.set('Fertig! Optimus und Bee stehen vor der Starter-Auswahl.\n' + directory.name)
            elif kind == 'skins':
                self.status_var.set('Figuren aktualisiert: Optimus Prime × Bumblebee. Ihr könnt euren Spielstand fortsetzen.')
            elif kind == 'error':
                self.status_var.set('Vorgang fehlgeschlagen. Eure Spielstände wurden nicht zurückgesetzt.')
                messagebox.showerror('Soul Link',value)
            elif kind == 'sync': self.sync_status.set(value)
        self.after(100,self.drain_events)

    def open_round(self) -> None:
        if self.creating:
            messagebox.showinfo('Bitte warten','Die neue Runde wird noch erstellt.'); return
        chosen = filedialog.askopenfilename(title='runde.json aus eurem Runden-Ordner öffnen',filetypes=[('Soul-Link-Runde','*.json')])
        if not chosen: return
        try:
            self.packs = {p.player:p for p in load_round(Path(chosen))}
            self.settings['manifest'] = chosen
            self._save()
            self.status_var.set('Runde geladen. Ihr könnt weiterspielen.')
        except (OSError,ValueError,KeyError,TypeError) as error:
            messagebox.showerror('Runde öffnen',str(error))

    def show_output(self) -> None:
        folder = Path(self.output_var.get()).expanduser().resolve()
        folder.mkdir(parents=True,exist_ok=True)
        if platform.system() == 'Windows': os.startfile(folder)
        else: subprocess.Popen(['open' if platform.system()=='Darwin' else 'xdg-open',str(folder)])

    def close(self) -> None:
        if self.creating:
            messagebox.showinfo('Bitte kurz warten','Die Runde wird noch bearbeitet.'); return
        self.stop_sync()
        self.destroy()

    def stop_sync(self) -> None:
        if self.sync_worker:
            self.sync_worker.stop()
            self.sync_worker = None
        if hasattr(self, "sync_status"):
            self.sync_status.set("Nicht verbunden")


def main() -> None:
    app = SoulLinkApp()
    app.mainloop()


if __name__ == "__main__":
    main()
