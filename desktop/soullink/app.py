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
from .online import WEBSITE, MirrorWorker, pairing, browser_url
from .cloud import CloudSession, CloudConflict


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
        self.mirror_worker = None
        self.cloud_session = None
        self.cloud_pending = False
        self.cloud_after_action = None
        self.pair_stop = threading.Event()
        self.pairing_active = False
        self.processes = {}
        self.runtime = {}
        self.creating = False
        self.update_busy = False
        self.update_info = None
        self.update_ready = None
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
        if self.connection_var.get(): self.sync_status.set('Verbunden · Cloud-Abgleich erfolgt vor dem Spielstart.')
        self.after(2500, self.check_updates)

    def _load(self) -> dict[str, object]:
        defaults: dict[str, object] = {
            "rom": "", "emulator": "", "output": str(Path.home() / "Downloads" / "SoulLink-Runden"),
            "scale": 4, "fps": 60, "volume": 80, "fullscreen": True, "player": "Optimus",
            "keys": dict(DEFAULT_KEYS), "connection": "", "save": "",
            "adventure": True, "pixel_filter": False, "integer_scaling": False, "screen_layout": "focus",
            "mirror": False,
        }
        try:
            loaded = json.loads(self.state_file.read_text(encoding="utf-8"))
            defaults.update(loaded)
        except (OSError, ValueError):
            pass
        from .melonds import preferred_emulator
        defaults['mirror']=False # Video retired; ignore older saved opt-ins.
        bundled = install_root() / 'Emulator' / ('melonDS.app' if platform.system() == 'Darwin' else 'melonDS.exe')
        defaults['emulator']=preferred_emulator(str(defaults['emulator']),bundled)
        from .controls import load_profile,key_label
        player=defaults.get('player','Optimus')
        if player in ('Optimus','Bee'):
            profile=load_profile(config_root(),player)
            defaults['keys']={**DEFAULT_KEYS,**defaults.get('keys',{}),
                **{key:key_label(value) for key,value in profile['Keyboard'].items() if key in DEFAULT_KEYS}}
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
            "mirror": bool(self.mirror_var.get()),
        })
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        from .cloud import atomic_write
        atomic_write(self.state_file,json.dumps(self.settings, indent=2, ensure_ascii=False).encode('utf-8'))

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
        game.add_command(label="Clone Wars: Anakin & Obi-Wan anwenden", command=self.apply_character_skins)
        game.add_separator()
        game.add_command(label="Anakin starten", command=lambda: self.start_player("Optimus"))
        game.add_command(label="Obi-Wan starten", command=lambda: self.start_player("Bee"))
        game.add_separator()
        game.add_command(label="Beenden", command=self.close)
        menu.add_cascade(label="Spiel", menu=game)
        menu.add_command(label="Emulator-Einstellungen", command=lambda: self.tabs.select(self.settings_tab))
        menu.add_command(label="Updates", command=lambda: self.tabs.select(self.update_tab))
        self.config(menu=menu)

    def _layout(self) -> None:
        top = ttk.Frame(self, padding=(30, 24, 30, 12))
        top.pack(fill="x")
        ttk.Label(top, text="SOUL LINK  /  FOCUS", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Dein Spiel im Mittelpunkt. Anakin × Obi-Wan · Windows + macOS", style="Sub.TLabel").pack(anchor="w", pady=(3, 0))
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
        self.update_tab = ttk.Frame(self.tabs, padding=22, style='Panel.TFrame')
        self.tabs.add(self.update_tab,text='Updates')
        self.update_status = tk.StringVar(value=f'Installiert: {__version__} · Update-Prüfung wird vorbereitet.')
        ttk.Label(self.update_tab,textvariable=self.update_status,style='Panel.TLabel',wraplength=780).pack(anchor='w',pady=12)
        ttk.Label(self.update_tab,text='Neue App separat installieren. Spielstände, Runden und alte App bleiben erhalten.\nWechsel erst nach dem Speichern, Schließen des Spiels und Cloud-Abgleich.\nJedi-Grafiken werden nicht ungefragt auf eure ROM angewendet.',style='Panel.TLabel',wraplength=780).pack(anchor='w',pady=8)
        row=ttk.Frame(self.update_tab,style='Panel.TFrame');row.pack(fill='x',pady=12)
        ttk.Button(row,text='Nach Updates suchen',command=self.check_updates).pack(side='left',padx=4)
        self.update_download=ttk.Button(row,text='Update herunterladen',command=self.download_update,state='disabled')
        self.update_download.pack(side='left',padx=4)
        self.update_start=ttk.Button(row,text='Zur neuen Version wechseln',command=self.activate_update,state='disabled')
        self.update_start.pack(side='left',padx=4)
        self.update_notes=tk.Text(self.update_tab,wrap='word',height=18,bg=COLORS['panel2'],fg=COLORS['text'],relief='flat')
        self.update_notes.pack(fill='both',expand=True);self.update_notes.configure(state='disabled')

    def check_updates(self):
        if self.update_busy: return
        self.update_busy=True
        self.update_status.set(f'Installiert: {__version__} · Prüfe stabile GitHub-Version …')
        def work():
            try:
                from .updater import check
                self.events.put(('update-found',check(__version__)))
            except Exception as error: self.events.put(('update-error',str(error)))
        threading.Thread(target=work,daemon=True).start()

    def download_update(self):
        if self.update_busy or not self.update_info: return
        info=dict(self.update_info)
        if not messagebox.askyesno('Update herunterladen',f"Version {info['version']} herunterladen ({info['size']/1024/1024:.0f} MB)?\n\nDie neue App wird separat abgelegt. Eure Runde und alte App werden nicht überschrieben."): return
        self.update_busy=True;self.update_download.state(['disabled'])
        self.update_start.state(['disabled']);self.update_ready=None
        def work():
            try:
                from .updater import prepare
                app=prepare(info,config_root()/'Updates',lambda n:self.events.put(('update-progress',n)))
                self.events.put(('update-ready',app))
            except Exception as error: self.events.put(('update-error',str(error)))
        threading.Thread(target=work,daemon=True).start()

    def activate_update(self):
        if not self.update_ready or self.update_busy: return
        if self.cloud_busy(): return
        if self.creating or self.pairing_active:
            messagebox.showinfo('Bitte warten','Rundenbearbeitung oder Website-Verbindung noch nicht abgeschlossen.');return
        if not messagebox.askyesno('Zur neuen App wechseln','Spiel gespeichert und Cloud-Abgleich abgeschlossen?\n\nDie neue Version wird gestartet und dieser Launcher geschlossen. Die alte App bleibt als Rückfalloption erhalten.'): return
        try:
            self.persist_controls(self.player_var.get())
            self._save()
            app=Path(self.update_ready)
            if not app.resolve().is_relative_to((config_root()/'Updates').resolve()): raise ValueError('Ungültiger Update-Pfad.')
            if platform.system()=='Darwin': subprocess.run(['open','-n',str(app)],check=True,timeout=20)
            else: subprocess.Popen([str(app)],cwd=app.parent)
            self.stop_sync();self.pair_stop.set();self.destroy()
        except Exception as error:
            messagebox.showerror('Update konnte nicht starten',str(error)+'\nDie bisherige App und eure Daten bleiben erhalten.')

    def _field(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, browse) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        ttk.Button(parent, text="Auswählen", command=browse).grid(row=row, column=2, pady=8)

    def _round_ui(self) -> None:
        tab = self.round_tab
        tab.columnconfigure((0,1), weight=1)
        ttk.Label(tab, text="Eure Runde. Euer Abenteuer.", style="Panel.TLabel", font=("Arial", 22, "bold")).grid(row=0,column=0,columnspan=2,sticky='w',pady=(4,8))
        ttk.Label(tab,text='Spieler auswählen und in Focus weiterspielen.',style='Panel.TLabel',foreground=COLORS['muted']).grid(row=1,column=0,columnspan=2,sticky='w')
        self.rom_var = tk.StringVar(value=str(self.settings["rom"]))
        self.emu_var = tk.StringVar(value=str(self.settings["emulator"]))
        self.output_var = tk.StringVar(value=str(self.settings["output"]))
        self.adventure_var = tk.BooleanVar(value=bool(self.settings['adventure']))
        self.status_var = tk.StringVar(value="Bereit für eine neue Runde.")
        self.player_cards=[]
        for column,(name,character) in enumerate((('Optimus','JOHN · ANAKIN SKYWALKER'),('Bee','EDDIE · OBI-WAN KENOBI'))):
            card=ttk.Frame(tab,padding=22,style='Panel.TFrame')
            self.player_cards.append(card)
            card.grid(row=2,column=column,sticky='ew',padx=(0,8) if column==0 else (8,0),pady=(24,12))
            ttk.Label(card,text=character,style='Panel.TLabel',foreground=COLORS['gold'],font=('Arial',10,'bold')).pack(anchor='w')
            display='Anakin' if name=='Optimus' else 'Obi-Wan'
            ttk.Label(card,text=display,style='Panel.TLabel',font=('Arial',28,'bold')).pack(anchor='w',pady=(8,16))
            ttk.Button(card,text=display+' starten',style='Primary.TButton',command=lambda p=name:self.start_player(p)).pack(fill='x')
        ttk.Label(tab,textvariable=self.status_var,style='Panel.TLabel',foreground=COLORS['green'],wraplength=760).grid(row=3,column=0,columnspan=2,sticky='w',pady=(4,16))
        self.cloud_status = tk.StringVar(value='Cloud-Spielstand: Website verbinden, dann vor jedem Spielstart automatisch abgleichen.')
        ttk.Label(tab,textvariable=self.cloud_status,style='Panel.TLabel',foreground=COLORS['gold'],wraplength=760).grid(row=6,column=0,columnspan=2,sticky='w',pady=(10,0))
        ttk.Button(tab,text='Cloud jetzt abgleichen · ohne Spielstart',command=self.cloud_only).grid(row=7,column=0,columnspan=2,sticky='ew',pady=(8,0))
        actions = ttk.Frame(tab, style="Panel.TFrame")
        actions.grid(row=4,column=0,columnspan=2,sticky='ew')
        actions.columnconfigure((0, 1), weight=1)
        self.create_button=ttk.Button(actions,text='+ Neue randomisierte Runde',command=self.create_new_round)
        self.create_button.grid(row=0,column=0,sticky='ew',padx=(0,7))
        ttk.Button(actions,text='Vorhandene Runde öffnen',command=self.open_round).grid(row=0,column=1,sticky='ew',padx=(7,0))
        ttk.Button(actions,text='Runden-Ordner anzeigen',command=self.show_output).grid(row=1,column=0,sticky='ew',padx=(0,7),pady=(10,0))
        ttk.Button(actions,text='Figuren aktualisieren',command=self.apply_character_skins).grid(row=1,column=1,sticky='ew',padx=(7,0),pady=(10,0))
        self.setup_panel=ttk.Frame(tab,style='Panel.TFrame')
        self.setup_panel.grid(row=8,column=0,columnspan=2,sticky='ew',pady=(6,0))
        self.setup_panel.columnconfigure(1,weight=1)
        self._field(self.setup_panel,0,'Originale SoulSilver-ROM',self.rom_var,self.pick_rom)
        self._field(self.setup_panel,1,'Focus / melonDS',self.emu_var,self.pick_emulator)
        self._field(self.setup_panel,2,'Runden-Ordner',self.output_var,self.pick_output)
        ttk.Checkbutton(self.setup_panel,text='Auch wilde Pokémon und gegnerische Teams randomisieren',variable=self.adventure_var).grid(row=3,column=0,columnspan=3,sticky='w',pady=(6,0))
        self.setup_panel.grid_remove()
        def toggle_setup():
            if self.setup_panel.winfo_manager():
                self.setup_panel.grid_remove()
                for card in self.player_cards: card.grid()
            else: self.show_setup()
        ttk.Button(tab,text='Dateien & Vorbereitung',command=toggle_setup).grid(row=5,column=0,columnspan=2,sticky='w',pady=(18,0))

    def show_setup(self) -> None:
        for card in self.player_cards: card.grid_remove()
        self.setup_panel.grid()

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
        self.key_baseline={name:str(keys.get(name,default)) for name,default in DEFAULT_KEYS.items()}
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
        ttk.Button(tab,text='Website verbinden · einmal im Browser bestätigen',style='Primary.TButton',command=self.connect_website).grid(row=0,column=0,columnspan=3,sticky='ew',pady=(0,12))
        self._field(tab, 1, "Spielstand", self.save_var, lambda: self.save_var.set(filedialog.askopenfilename(filetypes=[("Nintendo DS Save", "*.sav")]) or self.save_var.get()))
        ttk.Label(tab, text="Spieler", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Label(tab, text='Spieler wird aus der Verbindungsdatei erkannt.', style='Panel.TLabel').grid(row=2,column=1,sticky='w',padx=12)
        self.sync_status = tk.StringVar(value="Nicht verbunden")
        ttk.Button(tab, text="Spielstand-Synchronisierung starten", style="Primary.TButton", command=self.start_sync).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(22, 10))
        ttk.Button(tab, text="Tracker & Bildvorschau stoppen", command=self.stop_sync).grid(row=4, column=0, columnspan=3, sticky="ew")
        ttk.Label(tab, textvariable=self.sync_status, style="Panel.TLabel", foreground=COLORS["green"], wraplength=760).grid(row=5, column=0, columnspan=3, sticky="w", pady=15)
        self.mirror_var=tk.BooleanVar(value=bool(self.settings['mirror']))
        ttk.Label(tab,text='Bildübertragung entfernt · Bild und Ton bei Bedarf über Discord teilen.',style='Panel.TLabel').grid(row=6,column=0,columnspan=3,sticky='w',pady=12)
        self.mirror_status=tk.StringVar(value='Nur Teams, Fangdaten und gespeicherte Spielstände werden synchronisiert.')
        ttk.Label(tab,textvariable=self.mirror_status,style='Panel.TLabel',wraplength=750).grid(row=7,column=0,columnspan=3,sticky='w')
        ttk.Label(tab,text='Nach der Bestätigung verbindet sich die App automatisch. Teamdaten folgen nach\ndem Speichern im Spiel; K. o. nur bei gespeichertem Stand mit 0 KP.\nFür eine neue gemeinsame Spielrunde bitte auch eine neue Website-Runde verbinden.',style='Panel.TLabel',foreground=COLORS['muted']).grid(row=8,column=0,columnspan=3,sticky='w',pady=16)
        ttk.Button(tab,text='Gemeinsamen Tracker öffnen',command=self.open_website).grid(row=9,column=0,columnspan=3,sticky='ew')

    def connect_website(self):
        if self.cloud_busy(): return
        if self.pairing_active: return
        self.pair_stop.set();self.pair_stop=threading.Event()
        self.pairing_active=True
        def work():
            try: pairing(lambda url:self.events.put(('open-web',url)),
                lambda access:self.events.put(('paired',access)),lambda text:self.events.put(('sync',text)),self.pair_stop)
            finally: self.events.put(('pair-ended',None))
        threading.Thread(target=work,daemon=True).start()
        self.sync_status.set('Website wird geöffnet …')

    def online_access(self):
        if not self.connection_var.get(): return None
        try:
            data=json.loads(Path(self.connection_var.get()).read_text())
            browser_url(data)
            return data
        except (OSError,ValueError,KeyError): return None

    def open_website(self):
        access=self.online_access()
        webbrowser.open(browser_url(access) if access else WEBSITE)

    def save_mirror_preference(self):
        self._save()
        if self.mirror_worker:
            flag=self.mirror_worker.frame.with_name(self.mirror_worker.frame.name+'.enabled')
            if self.mirror_var.get(): flag.touch()
            else: flag.unlink(missing_ok=True)

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
        if self.cloud_busy(): return
        if self.creating: return
        if any(p.poll() is None for p in self.processes.values()):
            messagebox.showinfo('Neue Runde','Bitte zuerst das laufende Spiel schließen.'); return
        try:
            self._save()
        except (OSError,ValueError) as error:
            messagebox.showerror('Einstellungen',str(error)); return
        source, destination = Path(self.rom_var.get()), Path(self.output_var.get())
        if not self.rom_var.get() or not source.is_file():
            self.show_setup()
            messagebox.showinfo('Original-ROM auswählen','Bitte zuerst unter Dateien & Vorbereitung eure eigene deutsche SoulSilver-ROM auswählen.'); return
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
            self.persist_controls(self.player_var.get())
            self._save()
            messagebox.showinfo("Einstellungen", "Gespeichert. Die Einstellungen gelten beim nächsten Spielstart.")
        except Exception as error:
            messagebox.showerror("Einstellungen", str(error))

    def persist_controls(self,player,native=None):
        from .controls import load_profile,read_native,save_profile,key_label
        from .melonds import portable_directory
        profile=read_native(portable_directory(native)/'melonDS.toml') if native else load_profile(config_root(),player)
        if native is None:
            for key,var in self.key_vars.items():
                if key not in profile['Keyboard'] or var.get()!=self.key_baseline.get(key):
                    profile['Keyboard'][key]=qt_key(var.get())
        save_profile(config_root(),player,profile)
        for key,value in profile['Keyboard'].items():
            if key in self.key_vars:self.key_vars[key].set(key_label(value))
        self.key_baseline={key:var.get() for key,var in self.key_vars.items()}
        return profile

    def apply_character_skins(self) -> None:
        if self.cloud_busy(): return
        if self.creating: return
        if not self.packs:
            messagebox.showinfo('Figuren','Bitte zuerst eure vorhandene Runde öffnen.'); return
        if any(p.poll() is None for p in self.processes.values()):
            messagebox.showinfo('Figuren','Bitte zuerst das laufende Spiel schließen.'); return
        if not messagebox.askokcancel('Clone Wars: Anakin & Obi-Wan',
            'Bitte auch separat gestartete melonDS-Fenster schließen.\n\n'
            'John wird Anakin, Eddie wird Obi-Wan, jeweils mit Lichtschwert. '
            'Ersetzt Lauf-/Rennfiguren und Trainer-Kampfgrafiken durch Jedi. '
            'Eure Namen im Spiel werden Anakin und Obi-Wan. Fortschritt und Pokémon bleiben erhalten. '
            'ROMs und Spielstände werden vorher gesichert.\n\n'
            'Gegnernamen, Dialoge und Spezialaktionen (z. B. Radfahren) bleiben unverändert. '
            'Einige Zivilisten teilen ihre Grafik mit Trainern und bekommen ebenfalls den Jedi-Look. '
            'Für Gerätewechsel den vollständigen Rundenordner einschließlich der Grafik-Zuordnung kopieren; '
            'auf beiden Geräten Version 0.8 oder neuer verwenden.'):
            return
        from .jedi import apply_jedi
        packs = list(self.packs.values())
        self.creating = True
        self.create_button.state(['disabled'])
        self.status_var.set('Die Spielfiguren werden aktualisiert …')
        def work() -> None:
            try:
                from .identity import renamed_data,rename_save
                for pack in packs:
                    if pack.save:renamed_data(pack.save.read_bytes(),pack.player)
                for pack in packs:
                    apply_jedi(pack.rom,pack.player)
                    if pack.save:rename_save(pack.save,pack.player)
                self.events.put(('skins',None))
            except Exception as error:
                self.events.put(('error',str(error)))
        threading.Thread(target=work,daemon=True).start()

    def cloud_busy(self):
        if self.cloud_pending or self.cloud_session or any(p.poll() is None for p in self.processes.values()):
            messagebox.showinfo('Cloud-Spielstand','Bitte zuerst das Spielfenster schließen und den Cloud-Abgleich abwarten.')
            return True
        return False

    def cloud_only(self):
        access=self.online_access()
        if not access:
            messagebox.showinfo('Cloud-Spielstand','Bitte zuerst Website verbinden.');return
        self.start_player('Optimus' if access['player']=='John' else 'Bee',sync_only=True)

    def prepare_cloud(self, player, sync_only=False, choice=None):
        self.cloud_pending=True
        self.cloud_status.set('Cloud wird geprüft … Bitte noch nicht auf dem anderen Gerät starten.')
        session=self.cloud_session
        def work():
            try:
                session.prepare(choice)
                self.events.put(('cloud-ready',(player,sync_only)))
            except CloudConflict as error: self.events.put(('cloud-conflict',(player,sync_only,str(error))))
            except Exception as error:
                try: session.release()
                except Exception: pass
                self.events.put(('cloud-error',str(error)))
        threading.Thread(target=work,daemon=True).start()

    def finish_cloud(self):
        session=self.cloud_session
        if not session: return
        self.cloud_pending=True
        self.cloud_status.set('Letzter Spielstand wird gesichert … Bitte App noch offen lassen.')
        def work():
            try:
                session.finish()
                self.events.put(('cloud-finished',None))
            except Exception as error: self.events.put(('cloud-error',str(error)))
        threading.Thread(target=work,daemon=True).start()

    def start_player(self, player: str, _cloud_ready=False, sync_only=False) -> None:
        try:
            if self.cloud_pending: raise RuntimeError('Bitte den Cloud-Abgleich abwarten.')
            if self.pairing_active: raise RuntimeError('Bitte zuerst die Website-Verbindung im Browser bestätigen.')
            pack = self.packs.get(player)
            if self.creating: raise RuntimeError('Bitte warten, bis die Runde fertig ist.')
            if player in self.processes and self.processes[player].poll() is None:
                raise RuntimeError('Dieses Spiel läuft bereits.')
            if any(p.poll() is None for p in self.processes.values()):
                raise RuntimeError('Bitte das andere Spielfenster vor dem Spielerwechsel schließen.')
            if not pack:
                raise RuntimeError("Bitte zuerst eine neue randomisierte Runde erstellen.")
            input_profile=self.persist_controls(player)
            self._save()
            access=self.online_access()
            if self.connection_var.get() and not access:
                raise RuntimeError('Deine Website-Verbindung ist ungültig. Bitte vor dem Spielen erneut verbinden.')
            expected='John' if player=='Optimus' else 'Eddie'
            if access and access.get('player')!=expected:
                raise RuntimeError('Du bist als anderer Spieler verbunden. Bitte den eigenen Spieler starten.')
            if access and not _cloud_ready:
                self.stop_sync()
                self.cloud_session=CloudSession(access,pack.save,pack.rom,config_root()/'Cloud',lambda text:self.events.put(('cloud-status',text)))
                self.prepare_cloud(player,sync_only)
                return
            if sync_only:
                self.finish_cloud();return
            source = Path(self.emu_var.get()).expanduser().resolve()
            find_executable(source)
            isolated = config_root() / 'Emulator' / player
            isolated.mkdir(parents=True,exist_ok=True)
            executable = copy_emulator(source,isolated)
            write_config(executable, scale=int(self.scale_var.get()), fps=int(self.fps_var.get()),
                         volume_percent=int(self.volume_var.get()),
                         keys={name: value.get() for name, value in self.key_vars.items()},
                         save_directory=pack.rom.parent,pixel_filter=self.filter_var.get()=='Weich',
                         integer_scaling=bool(self.integer_var.get()),screen_layout=str(self.settings['screen_layout']),
                         pause_lost_focus=False,input_profile=input_profile)
            request=config_root()/'requests'/(uuid.uuid4().hex+'.json')
            request.parent.mkdir(parents=True,exist_ok=True)
            self.stop_sync()
            mirror=None
            self.processes[player] = launch(executable, pack.rom, fullscreen=bool(self.fullscreen_var.get()),player=player,request=request,
                                           mirror=mirror,website=browser_url(access) if access else '')
            self.runtime[player]=(executable,request)
            self.save_var.set(str(pack.save))
            self._save()
            if access:
                self.cloud_session.start()
                self.start_sync()
            else: self.sync_status.set('Für diesen Spieler bitte einmal Website verbinden.')
            self.withdraw()
        except Exception as error:
            if _cloud_ready and self.cloud_session and not self.cloud_pending and not any(p.poll() is None for p in self.processes.values()): self.finish_cloud()
            messagebox.showerror("Spiel starten", str(error))

    def start_sync(self) -> None:
        try:
            if not self.cloud_session or self.cloud_pending:
                self.sync_status.set('Cloud und Tracker werden beim Spielstart gemeinsam abgeglichen.');return
            if self.sync_worker: self.sync_worker.stop()
            self.sync_worker=None
            self._save()
            if not self.connection_var.get() or not self.save_var.get():
                self.sync_status.set('Bitte zuerst Website verbinden und euer Spiel starten.');return
            access=self.online_access()
            if access:
                expected='Optimus' if access.get('player')=='John' else 'Bee'
                if expected not in self.packs or Path(self.save_var.get()).resolve()!=self.packs[expected].save.resolve():
                    self.sync_status.set('Diese Website-Verbindung gehört zum anderen Spieler.');return
            request=self.runtime.get(expected,(None,None))[1] if access else None
            self.sync_worker = SyncWorker(Path(self.connection_var.get()), Path(self.save_var.get()), lambda text: self.events.put(('sync',text)),team=request.with_suffix('.team') if request else None)
            self.sync_worker.start()
            self.sync_status.set("Verbindung wird aufgebaut …")
        except Exception as error:
            messagebox.showerror("Live-Verbindung", str(error))

    def drain_events(self) -> None:
        for player,(executable,request) in list(self.runtime.items()):
            process=self.processes[player]
            if process.poll() is None: continue
            if self.cloud_session: self.finish_cloud()
            if self.sync_worker: self.sync_worker.stop();self.sync_worker=None
            if self.mirror_worker:
                flag=self.mirror_worker.frame.with_name(self.mirror_worker.frame.name+'.enabled')
                self.mirror_var.set(flag.exists())
                self.mirror_worker.stop();self.mirror_worker=None
            del self.runtime[player]
            try:
                self.persist_controls(player,native=executable)
                self._save()
            except (OSError,ValueError,KeyError,TypeError):
                self.status_var.set('Tastenprofil konnte nicht übernommen werden; die letzte Sicherung bleibt erhalten.')
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
                if self.cloud_pending: self.cloud_after_action=action
                else: self.run_after_game(action)
            except (OSError,ValueError,AttributeError): pass
        while not self.events.empty():
            kind,value = self.events.get_nowait()
            if kind.startswith('update-'):
                if kind=='update-progress': self.update_status.set(f'Update herunterladen: {value}% · Danach Prüfsumme und Paket prüfen …')
                elif kind=='update-ready':
                    self.update_busy=False;self.update_ready=value
                    self.update_status.set('Update geprüft und bereit. Nach Spielende zur neuen Version wechseln.\nNeue App: '+str(value))
                    self.update_start.state(['!disabled'])
                elif kind=='update-error':
                    self.update_busy=False;self.update_status.set('Update nicht verfügbar: '+value+' · Eure App bleibt unverändert.')
                    if self.update_info:self.update_download.state(['!disabled'])
                elif kind=='update-found':
                    self.update_busy=False;self.update_info=value
                    self.update_download.state(['!disabled'] if value else ['disabled'])
                    self.tabs.tab(self.update_tab,text='Updates · NEU' if value else 'Updates')
                    self.update_status.set(f"Installiert: {__version__} · Neue Version: {value['version']}" if value else f'Installiert: {__version__} · Kein neuerer stabiler Release verfügbar.')
                    self.update_notes.configure(state='normal');self.update_notes.delete('1.0','end')
                    self.update_notes.insert('1.0',value['notes'] if value else 'Ihr verwendet bereits den neuesten verfügbaren Stand.');self.update_notes.configure(state='disabled')
                continue
            if kind=='pair-ended': self.pairing_active=False
            if kind=='cloud-status': self.cloud_status.set(value)
            elif kind=='cloud-ready':
                self.cloud_pending=False
                self.start_player(value[0],_cloud_ready=True,sync_only=value[1])
            elif kind=='cloud-conflict':
                player,sync_only,detail=value
                answer=messagebox.askyesnocancel('Spielstand auswählen',detail+'\n\nJa: Cloud-Stand laden (lokale Sicherung wird angelegt).\nNein: Lokalen Stand zur neuen Cloud-Version machen.\nAbbrechen: Nichts ändern, Spiel nicht starten.')
                if answer is None:
                    session=self.cloud_session
                    def cancel():
                        try: session.release()
                        except Exception: pass
                        self.events.put(('cloud-cancelled',None))
                    threading.Thread(target=cancel,daemon=True).start()
                else: self.prepare_cloud(player,sync_only,'cloud' if answer else 'local')
            elif kind in ('cloud-finished','cloud-error','cloud-cancelled'):
                self.cloud_pending=False;self.cloud_session=None
                action=self.cloud_after_action;self.cloud_after_action=None
                if kind=='cloud-finished':
                    self.cloud_status.set('Cloud gesichert · Gerätewechsel möglich')
                    self.run_after_game(action)
                elif kind=='cloud-error':
                    self.cloud_status.set('Nicht in der Cloud gesichert · lokaler Stand bleibt erhalten. Erneut abgleichen!')
                    messagebox.showerror('Cloud-Spielstand',str(value)+'\n\nVor dem Gerätewechsel „Cloud jetzt abgleichen“ erneut versuchen.')
                else: self.cloud_status.set('Abgleich abgebrochen · beide Spielstände unverändert')
            if kind in ('round','skins','error'):
                self.creating = False
                self.create_button.state(['!disabled'])
            if kind == 'round':
                directory,packs = value
                self.packs = {p.player:p for p in packs}
                self.settings['manifest'] = str(directory / 'runde.json')
                self.stop_sync()
                self.connection_var.set('')
                self._save()
                self.status_var.set('Fertig! Anakin und Obi-Wan stehen vor der Starter-Auswahl.\n' + directory.name)
            elif kind == 'skins':
                self.status_var.set('Figuren aktualisiert: Anakin × Obi-Wan mit Lichtschwertern. Euer Spielstand bleibt erhalten.')
            elif kind == 'error':
                self.status_var.set('Vorgang fehlgeschlagen. Eure Spielstände wurden nicht zurückgesetzt.')
                messagebox.showerror('Soul Link',value)
            elif kind == 'sync': self.sync_status.set(value)
            elif kind == 'mirror': self.mirror_status.set(value)
            elif kind == 'open-web': webbrowser.open(value)
            elif kind == 'paired':
                self.stop_sync()
                connection=config_root()/'website-connection.json'
                connection.parent.mkdir(parents=True,exist_ok=True)
                connection.write_text(json.dumps(value),encoding='utf-8')
                if os.name!='nt': connection.chmod(0o600)
                self.connection_var.set(str(connection))
                player='Optimus' if value['player']=='John' else 'Bee'
                if player in self.packs: self.save_var.set(str(self.packs[player].save))
                self._save();self.start_sync()
                display='Anakin' if player=='Optimus' else 'Obi-Wan'
                self.sync_status.set(f'{display} verbunden. Beim nächsten Spielstart ist auch die Bildvorschau bereit.')
        self.after(100,self.drain_events)

    def open_round(self) -> None:
        if self.cloud_busy(): return
        if self.creating:
            messagebox.showinfo('Bitte warten','Die neue Runde wird noch erstellt.'); return
        chosen = filedialog.askopenfilename(title='runde.json aus eurem Runden-Ordner öffnen',filetypes=[('Soul-Link-Runde','*.json')])
        if not chosen: return
        try:
            self.packs = {p.player:p for p in load_round(Path(chosen))}
            self.settings['manifest'] = chosen
            self.stop_sync()
            self.connection_var.set('')
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
        if self.cloud_busy(): return
        if self.creating:
            messagebox.showinfo('Bitte kurz warten','Die Runde wird noch bearbeitet.'); return
        self.stop_sync()
        self.pair_stop.set()
        self.destroy()

    def run_after_game(self,action):
        if action=='new-round': self.after(200,self.create_new_round)
        elif action=='connect-website': self.after(200,self.connect_website)
        elif action in ('start:Optimus','start:Bee'):
            self.after(200,lambda p=action.split(':')[1]:self.start_player(p))

    def stop_sync(self) -> None:
        if self.mirror_worker:
            self.mirror_worker.stop();self.mirror_worker=None
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
