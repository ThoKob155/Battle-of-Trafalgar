# -*- coding: utf-8 -*-
"""
BATTLE OF TRAFALGAR
===================
Schiffe versenken im Stil einer Seeschlacht um 1800.
Mensch gegen Computer oder Mensch gegen Mensch (zwei Spieler an einem Rechner, "Hotseat").
Jede Nation hat eine eigene Flotte und eigene Truhenpreise.
Umgesetzt mit Python 3 und tkinter (keine Installation noetig).

Starten:   python battle_of_trafalgar.py

Aufbau der Datei (strukturiert):
  1. Konstanten
  2. Spiellogik        (reine Funktionen auf einfachen Datenstrukturen, ohne Grafik)
  3. Computergegner    (drei Schwierigkeitsgrade)
  4. Speichern/Laden   (Name, Einstellungen, Punkte in trafalgar_save.json)
  5. Zeichenfunktionen (Bilder, Schiffe, Spielfelder werden per Code gezeichnet)
  6. Oberflaeche       (Klasse TrafalgarApp: Bildschirme und Mausbedienung)

Eigene Bilder (optional): Lege "start.png" und "interior.png" in einen Ordner "assets"
neben diese Datei.  Mit installiertem Pillow (pip install pillow) werden sie automatisch
auf Fenstergroesse skaliert, sonst muessen sie 1100 x 700 Pixel gross sein.
"""

import json
import math
import os
import random
import shutil
import subprocess
import sys
import tkinter as tk
from datetime import datetime

# ======================================================================
# 1. KONSTANTEN
# ======================================================================
WIDTH, HEIGHT = 1100, 700
GRID = 10
LETTERS = "ABCDEFGHIJ"
FONT = "Georgia"

DIFFICULTIES = ["New Entrant", "Lieutenant-Commander", "Admiral"]
NATIONS = ["Spain", "France", "England"]
NATION_COLORS = {
    "Spain": ("#c60b1e", "#ffc400"),
    "France": ("#0055a4", "#ef4135"),
    "England": ("#cf142b", "#f4f1e8"),
}

# Flotten je Nation: (Name, Art, Groesse in Kaestchen, Anzahl) - das groesste Schiff zuerst.
# Jede Flotte hat genau 31 Kaestchen, damit alle Nationen gleich fair sind.
NATION_FLEETS = {
    "France": [("Fleet Flagship", "flagship", 5, 1), ("Gunship", "gunship", 4, 2),
               ("Frigate", "frigate", 3, 3), ("Post Ship", "post", 2, 4),
               ("Treasure Ship", "treasure", 1, 1)],
    "Spain": [("Fleet Flagship", "flagship", 5, 2), ("Gunship", "gunship", 4, 2),
              ("Frigate", "frigate", 3, 4), ("Treasure Ship", "treasure", 1, 1)],
    "England": [("Gunship", "gunship", 4, 2), ("Frigate", "frigate", 3, 4),
                ("Post Ship", "post", 2, 5), ("Treasure Ship", "treasure", 1, 1)],
}

# Truhenpreise je Nation (einer davon wird zufaellig gezogen)
NATION_PRIZES = {
    "England": ["broadside", "signals", "reinforcement"],
    "France": ["mortar", "fireship", "gunners"],
    "Spain": ["gold", "repair", "map"],
}
# Kurzerklaerung der Unterschiede, wird unter den Flaggen angezeigt
NATION_INFO_DE = {
    "Spain": "Spanien: 2 Flottenflaggschiffe und mehr große Schiffe, keine Postschiffe.\n"
             "Schatzkiste: Dublonen, Reparaturtrupp, Schatzkarte",
    "France": "Frankreich: ausgewogene Flotte (1 Flaggschiff, 4 Postschiffe).\n"
              "Schatzkiste: Mörserfeuer, Brander, Veteranen-Kanoniere",
    "England": "England: kein Flaggschiff, dafür 5 kleine Postschiffe.\n"
               "Schatzkiste: Breitseite, Signalflaggen, Verstärkung",
}
# Texte der Einfuehrungsseite
INTRO_NATIONS_DE = {
    "Spain": "2 Flaggschiffe, 2 Kanonenschiffe, 4 Fregatten, keine Postschiffe.\n"
             "Truhe: Dublonen, Reparaturtrupp, Schatzkarte",
    "France": "1 Flaggschiff, 2 Kanonenschiffe, 3 Fregatten, 4 Postschiffe.\n"
              "Truhe: Mörserfeuer, Brander, Veteranen-Kanoniere",
    "England": "2 Kanonenschiffe, 4 Fregatten, 5 Postschiffe, kein Flaggschiff.\n"
               "Truhe: Breitseite, Signalflaggen, Verstärkung",
}
INTRO_LEVELS_DE = [
    ("New Entrant", "Der Gegner schießt blind auf zufällige Felder. Ideal zum Üben."),
    ("Lieutenant-Commander", "Der Gegner sucht im Schachbrettmuster und verfolgt getroffene Schiffe."),
    ("Admiral", "Der Gegner berechnet für jedes Feld, wo noch Schiffe liegen können. Der härteste Gegner."),
]
PRIZE_INTRO_DE = ("Das Schatzschiff hat nur ein Kästchen. Wird es getroffen, öffnet sich eine Truhe mit einem zufälligen "
                  "Preis deiner Nation. Er liegt im Cargo hold und kann ab deinem nächsten Zug mit Linksklick eingesetzt "
                  "werden. Jeder Spieler hat nur ein Schatzschiff, also gibt es höchstens eine Truhe pro Spiel.")
PRIZE_TEXT_DE = {
    "broadside": ("Breitseite", "Dein nächster Schuss trifft 3 Felder in einer Reihe (waagrecht, das angeklickte Feld in der Mitte)."),
    "signals": ("Signalflaggen", "4 zufällige Felder des Gegners werden aufgedeckt: Raute = Schiff, Punkt = Wasser. Sie werden nicht beschossen."),
    "reinforcement": ("Verstärkung", "Du erhältst ein neues Schiff mit 1 Kästchen und setzt es selbst auf ein freies Feld deiner Flotte."),
    "mortar": ("Mörserfeuer", "Dein nächster Schuss trifft einen 2x2-Block, der am angeklickten Feld beginnt."),
    "fireship": ("Brander", "Der Gegner setzt seinen nächsten Zug aus. Du schießt also zweimal hintereinander."),
    "gunners": ("Veteranen-Kanoniere", "Du bekommst sofort einen Extraschuss in diesem Zug."),
    "gold": ("Dublonen", "Du bekommst sofort 5 Punkte (zählt für die Hall of Fame)."),
    "repair": ("Reparaturtrupp", "Ein getroffenes Feld eines noch schwimmenden Schiffes deiner Flotte wird repariert und kann erneut getroffen werden."),
    "map": ("Schatzkarte", "Ein ganzes gegnerisches Schiff wird auf der Karte markiert, und sein Typ wird gemeldet."),
}
INTRO_STEPS_DE = [
    "Name eingeben, Gegner (Computer oder zweiter Spieler), Schwierigkeitsgrad und Nation wählen. Jede Nation hat gleich viele Felder, aber eine andere Anzahl und Größe von Schiffen.",
    "Flotte platzieren: Linksklick setzt ein Schiff, rechte Maustaste oder Taste R dreht es. \"Random\" setzt zufällig, \"Reset\" räumt auf.",
    "Abwechselnd schießen, den Start bestimmt der Zufall. Schuss = rechte Maustaste (am Mac auch Control-Klick) auf das linke Feld, das Gewässer des Gegners.",
    "Rot = Treffer, Blau = Fehlschuss, Gold = Schatzschiff. Ein versenktes Schiff zeigt Totenköpfe.",
    "Schatzschiff getroffen: Die Truhe liefert einen Preis für den Cargo hold. Er ist ab der nächsten Runde mit Linksklick einsetzbar und bleibt dem Gegner verborgen.",
    "Jedes getroffene Schiffsfeld = 1 Punkt. Sieger ist, wer alle gegnerischen Schiffe außer dem Schatzschiff versenkt. Die Punkte werden gespeichert (Hall of Fame).",
    "Zu zweit (Hotseat) wird der Bildschirm bei jedem Wechsel verdeckt: Computer weitergeben und bestätigen.",
]

# Namen der Admirale, die der Computer je nach Nation traegt
COMMANDERS = {
    "France": "Pierre Charles de Villeneuve",
    "Spain": "Federico Carlos Gravina y Nápoli",
    "England": "Horatio Nelson, 1st Viscount Nelson",
}
PRIZE_INFO = {
    "broadside": ("Broadside!", "The next shot hits 3 squares in a row."),
    "signals": ("Signal Flags!", "Four enemy squares are revealed."),
    "reinforcement": ("Royal Reinforcement!", "A new 1-square ship joins the fleet."),
    "mortar": ("Mortar Barrage!", "The next shot hits a 2x2 block."),
    "fireship": ("Fireship!", "The enemy loses the next turn."),
    "gunners": ("Veteran Gunners!", "One extra shot."),
    "gold": ("Gold Doubloons!", "+5 points."),
    "repair": ("Repair Crew!", "One damaged square is repaired."),
    "map": ("Treasure Map!", "One enemy ship is marked on the chart."),
}
# Kurzname und Kurzbeschreibung fuer die Felder im Laderaum
PRIZE_SHORT = {
    "broadside": ("Broadside", "3 in a row"),
    "signals": ("Signal Flags", "reveal 4"),
    "reinforcement": ("Reinforcement", "+1 ship"),
    "mortar": ("Mortar", "2x2 block"),
    "fireship": ("Fireship", "foe skips turn"),
    "gunners": ("Gunners", "+1 shot"),
    "gold": ("Doubloons", "+5 points"),
    "repair": ("Repair Crew", "fix 1 hit"),
    "map": ("Treasure Map", "mark a ship"),
}
MAX_CARGO = 1     # es gibt nur ein Schatzschiff -> hoechstens ein Preis pro Spieler

# Farben
SEA_CHART = "#dcc99b"
CHART_LINE = "#9c8454"
HIT_RED = "#c0392b"
MISS_BLUE = "#2f7fe0"
TREASURE_GOLD = "#f2b705"
PARCHMENT = "#e8d7a8"
INK = "#3a2512"
GOLD = "#e6c875"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "trafalgar_save.json")
ASSET_DIR = os.path.join(BASE_DIR, "assets")

# Position und Kaestchengroesse der Spielfelder
BATTLE_ENEMY_POS = (70, 150)
BATTLE_OWN_POS = (650, 150)
BATTLE_CELL = 38
PLACE_POS = (70, 150)
PLACE_CELL = 44


# ======================================================================
# 2. SPIELLOGIK
# ======================================================================
def build_fleet(nation):
    """Erzeugt die Liste aller Schiffe der Flotte einer Nation."""
    fleet = []
    for name, kind, size, count in NATION_FLEETS[nation]:
        for _ in range(count):
            fleet.append({"name": name, "kind": kind, "size": size})
    return fleet


def new_board(nation):
    """Ein Spielfeld: Schiffe, empfangene Schuesse und vom Gegner ausgespaehte Felder."""
    return {"ships": [], "shots": {}, "scouted": {}, "nation": nation}


def in_grid(r, c):
    return 0 <= r < GRID and 0 <= c < GRID


def cell_name(cell):
    return LETTERS[cell[1]] + str(cell[0] + 1)


def ship_cells(r, c, size, horizontal):
    if horizontal:
        return [(r, c + i) for i in range(size)]
    return [(r + i, c) for i in range(size)]


def ship_at(board, cell):
    for ship in board["ships"]:
        if cell in ship["cells"]:
            return ship
    return None


def is_sunk(ship):
    return len(ship["hits"]) >= ship["size"]


def can_place(board, cells):
    for (r, c) in cells:
        if not in_grid(r, c) or ship_at(board, (r, c)) is not None:
            return False
    return True


def add_ship(board, entry, cells, ship_id=None):
    ship = {"name": entry["name"], "kind": entry["kind"], "size": entry["size"],
            "cells": list(cells), "hits": set(), "id": ship_id}
    board["ships"].append(ship)
    return ship


def place_randomly(board, entry, ship_id=None):
    """Platziert ein Schiff an einer zufaelligen freien Stelle.
    Bereits beschossene Felder werden gemieden (sonst waere das Schiff nie versenkbar)."""
    for _ in range(2000):
        horizontal = random.choice([True, False])
        cells = ship_cells(random.randrange(GRID), random.randrange(GRID),
                           entry["size"], horizontal)
        if can_place(board, cells) and not any(cell in board["shots"] for cell in cells):
            return add_ship(board, entry, cells, ship_id)
    return None


def place_fleet_randomly(board, fleet):
    """Platziert die ganze Flotte zufaellig (grosse Schiffe zuerst)."""
    order = sorted(range(len(fleet)), key=lambda i: -fleet[i]["size"])
    while True:
        board["ships"] = []
        ok = True
        for i in order:
            if place_randomly(board, fleet[i], i) is None:
                ok = False
                break
        if ok:
            return


def fire(board, cell):
    """Schuss auf ein Feld.  Ergebnis: miss / hit / treasure."""
    ship = ship_at(board, cell)
    if ship is None:
        board["shots"][cell] = "miss"
        return {"result": "miss", "ship": None, "sunk": False}
    ship["hits"].add(cell)
    result = "treasure" if ship["kind"] == "treasure" else "hit"
    board["shots"][cell] = result
    return {"result": result, "ship": ship, "sunk": is_sunk(ship)}


def fleet_defeated(board):
    """Verloren, wenn alle Schiffe ausser dem Schatzschiff versenkt sind."""
    real = [s for s in board["ships"] if s["kind"] != "treasure"]
    return len(real) > 0 and all(is_sunk(s) for s in real)


def ships_afloat(board):
    return sum(1 for s in board["ships"] if s["kind"] != "treasure" and not is_sunk(s))


def scout_cells(board, count=4):
    """Deckt zufaellige, noch nicht beschossene Felder auf (Truhenpreis 3)."""
    free = [(r, c) for r in range(GRID) for c in range(GRID)
            if (r, c) not in board["shots"] and (r, c) not in board["scouted"]]
    chosen = random.sample(free, min(count, len(free)))
    for cell in chosen:
        board["scouted"][cell] = ship_at(board, cell) is not None
    return chosen


def pattern_cells(kind, cell):
    """Felder, die ein Spezialschuss trifft: Broadside = 3 in einer Reihe, Mortar = 2x2."""
    r, c = cell
    if kind == "broadside":
        c0 = min(max(c - 1, 0), GRID - 3)
        return [(r, c0 + i) for i in range(3)]
    if kind == "mortar":
        r0, c0 = min(r, GRID - 2), min(c, GRID - 2)
        return [(r0 + i, c0 + j) for i in range(2) for j in range(2)]
    return [cell]


def repair_one(board):
    """Preis 'Repair Crew': ein getroffenes Feld wird wieder unbeschossen.
    Gibt das reparierte Feld zurueck (oder None, wenn nichts zu reparieren war)."""
    options = []
    for cell, res in board["shots"].items():
        if res == "hit":
            ship = ship_at(board, cell)
            if ship is not None and not is_sunk(ship):
                options.append(cell)
    if not options:
        options = [cell for cell, res in board["shots"].items() if res == "hit"]
    if not options:
        return None
    cell = random.choice(options)
    ship_at(board, cell)["hits"].discard(cell)
    del board["shots"][cell]
    board["scouted"].pop(cell, None)
    return cell


def reveal_ship(board):
    """Preis 'Treasure Map': markiert alle noch unbeschossenen Felder eines Schiffs."""
    options = [s for s in board["ships"] if s["kind"] != "treasure" and not is_sunk(s)
               and any(cell not in board["shots"] for cell in s["cells"])]
    if not options:
        return None
    ship = random.choice(options)
    for cell in ship["cells"]:
        if cell not in board["shots"]:
            board["scouted"][cell] = True
    return ship


# ======================================================================
# 3. COMPUTERGEGNER
# ======================================================================
def unshot_cells(board):
    return [(r, c) for r in range(GRID) for c in range(GRID) if (r, c) not in board["shots"]]


def active_hits(board):
    """Treffer auf Schiffen, die noch nicht versenkt sind."""
    result = []
    for cell, res in board["shots"].items():
        if res == "hit":
            ship = ship_at(board, cell)
            if ship is not None and not is_sunk(ship):
                result.append(cell)
    return result


def ai_choose_shot(board, difficulty):
    """Waehlt das Ziel des Computers.  board ist das Spielfeld des Menschen."""
    unshot = unshot_cells(board)
    if difficulty == "New Entrant":
        return random.choice(unshot)

    known_ships = [cell for cell, has in board["scouted"].items()
                   if has and cell not in board["shots"]]
    if known_ships:
        return random.choice(known_ships)
    known_empty = {cell for cell, has in board["scouted"].items() if not has}
    candidates = [cell for cell in unshot if cell not in known_empty] or unshot

    if difficulty == "Lieutenant-Commander":
        return ai_medium(board, candidates)
    return ai_admiral(board, candidates)


def ai_medium(board, candidates):
    """Zufaellig im Schachbrettmuster suchen, nach einem Treffer die Nachbarn beschiessen."""
    cand_set = set(candidates)
    active = set(active_hits(board))
    if active:
        near, line = [], []
        for (r, c) in active:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cand_set:
                    near.append(nb)
                    if (r - dr, c - dc) in active:
                        line.append(nb)
        pool = line or near
        if pool:
            return random.choice(pool)
    parity = [cell for cell in candidates if (cell[0] + cell[1]) % 2 == 0]
    return random.choice(parity or candidates)


def ai_admiral(board, candidates):
    """Wahrscheinlichkeitsfeld: Jedes noch moegliche Schiff wird in alle freien Lagen
    gelegt, Felder mit vielen Moeglichkeiten (vor allem neben Treffern) werden bevorzugt."""
    remaining = []
    for _name, _kind, size, count in NATION_FLEETS[board["nation"]]:
        remaining.extend([size] * count)
    for ship in board["ships"]:
        if is_sunk(ship) and ship["size"] in remaining:
            remaining.remove(ship["size"])

    shots = board["shots"]
    active = set(active_hits(board))
    blocked = {cell for cell in shots if cell not in active}
    blocked |= {cell for cell, has in board["scouted"].items() if not has}

    weights = {}
    for size in remaining:
        for r in range(GRID):
            for c in range(GRID):
                for horizontal in (True, False):
                    cells = ship_cells(r, c, size, horizontal)
                    if any((not in_grid(x, y)) or (x, y) in blocked for x, y in cells):
                        continue
                    hits_in = sum(1 for cell in cells if cell in active)
                    weight = 10 ** hits_in
                    for cell in cells:
                        if cell not in shots:
                            weights[cell] = weights.get(cell, 0) + weight
    options = {cell: w for cell, w in weights.items() if cell in set(candidates)}
    if not options:
        return random.choice(candidates)
    best = max(options.values())
    return random.choice([cell for cell, w in options.items() if w == best])


# ======================================================================
# 4. SPEICHERN / LADEN
# ======================================================================
def load_data():
    default = {"last_name": "", "last_name2": "", "last_nation": "England",
               "last_difficulty": "New Entrant", "last_mode": "ai", "sound": True,
               "players": {}, "history": []}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, value in default.items():
            data.setdefault(key, value)
        return data
    except (OSError, ValueError):
        return default


def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def record_result(data, name, points, won, difficulty):
    """Speichert das Ergebnis und gibt die Gesamtpunktzahl des Spielers zurueck."""
    player = data["players"].setdefault(name, {"total": 0, "games": 0, "wins": 0})
    player["total"] += points
    player["games"] += 1
    player["wins"] += 1 if won else 0
    data["history"].append({"name": name, "points": points, "won": won,
                            "difficulty": difficulty,
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
    data["history"] = data["history"][-100:]
    save_data(data)
    return player["total"]


# ======================================================================
# 5. ZEICHENFUNKTIONEN
# ======================================================================
def hex_to_rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, t):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_gradient(c, x0, y0, x1, y1, top, bottom, steps=40):
    height = (y1 - y0) / steps
    for i in range(steps):
        color = mix(top, bottom, i / max(1, steps - 1))
        c.create_rectangle(x0, y0 + i * height, x1, y0 + (i + 1) * height + 1,
                           fill=color, outline="")


def draw_parchment(c, x0, y0, x1, y1):
    c.create_rectangle(x0 + 5, y0 + 6, x1 + 5, y1 + 6, fill="#1a0f08", outline="")
    c.create_rectangle(x0, y0, x1, y1, fill=PARCHMENT, outline="#5a3a1e", width=5)
    c.create_rectangle(x0 + 10, y0 + 10, x1 - 10, y1 - 10, outline="#b89a5a", width=1)


def draw_flag(c, nation, x, y, w, h, tags=()):
    if nation == "Spain":
        c.create_rectangle(x, y, x + w, y + h * 0.25, fill="#c60b1e", outline="", tags=tags)
        c.create_rectangle(x, y + h * 0.25, x + w, y + h * 0.75, fill="#ffc400", outline="", tags=tags)
        c.create_rectangle(x, y + h * 0.75, x + w, y + h, fill="#c60b1e", outline="", tags=tags)
    elif nation == "France":
        c.create_rectangle(x, y, x + w / 3, y + h, fill="#0055a4", outline="", tags=tags)
        c.create_rectangle(x + w / 3, y, x + 2 * w / 3, y + h, fill="#ffffff", outline="", tags=tags)
        c.create_rectangle(x + 2 * w / 3, y, x + w, y + h, fill="#ef4135", outline="", tags=tags)
    else:
        c.create_rectangle(x, y, x + w, y + h, fill="#f4f1e8", outline="", tags=tags)
        c.create_rectangle(x + w * 0.42, y, x + w * 0.58, y + h, fill="#cf142b", outline="", tags=tags)
        c.create_rectangle(x, y + h * 0.38, x + w, y + h * 0.62, fill="#cf142b", outline="", tags=tags)
    c.create_rectangle(x, y, x + w, y + h, outline="#2a1a10", width=2, tags=tags)


def draw_tall_ship(c, x, y, s, facing, sail="#efe3c2", flag="#c60b1e", burning=False, rng=None):
    """Zeichnet ein grosses Segelschiff.  (x, y) = Wasserlinie, s = Massstab, facing = +1/-1."""
    f = facing
    rng = rng or random.Random(1)

    def P(px, py):
        return (x + f * px * s, y + py * s)

    def flat(points):
        out = []
        for px, py in points:
            out.extend(P(px, py))
        return out

    c.create_polygon(flat([(-115, -26), (118, -34), (96, 10), (-88, 10)]),
                     fill="#2a1a10", outline="#0d0805")
    c.create_polygon(flat([(-112, -17), (116, -23), (114, -17), (-110, -11)]),
                     fill="#d9a441", outline="")
    for i in range(6):
        a = P(-85 + i * 30, -9)
        b = P(-75 + i * 30, -3)
        c.create_rectangle(a[0], a[1], b[0], b[1], fill="#0d0805", outline="#c9983a")
    for mx, h in [(-62, 140), (0, 170), (62, 130)]:
        base, top = P(mx, -30), P(mx, -30 - h)
        c.create_line(base[0], base[1], top[0], top[1], fill="#1a0f08", width=max(2, int(4 * s)))
        sail_h = h * 0.27
        for k in range(3):
            y_bot = -38 - k * (sail_h + 6)
            y_top = y_bot - sail_h
            w_bot = 40 - k * 7
            w_top = w_bot - 4
            c.create_polygon(flat([(mx - w_top, y_top), (mx + w_top, y_top),
                                   (mx + w_bot, y_bot), (mx - w_bot, y_bot)]),
                             fill=sail, outline="#8a7a55")
        c.create_polygon(top[0], top[1], top[0] + f * 26 * s, top[1] + 6 * s,
                         top[0], top[1] + 12 * s, fill=flag, outline="")
    a, b = P(115, -32), P(160, -52)
    c.create_line(a[0], a[1], b[0], b[1], fill="#1a0f08", width=max(2, int(3 * s)))
    if burning:
        for i in range(6):
            px = -75 + i * 28
            hh = rng.randint(45, 85)
            c.create_polygon(flat([(px - 12, -30), (px, -30 - hh), (px + 12, -30)]),
                             fill="#e8590c", outline="")
            c.create_polygon(flat([(px - 6, -30), (px, -30 - hh * 0.6), (px + 6, -30)]),
                             fill="#ffd23f", outline="")
        for i in range(8):
            px, py = rng.randint(-80, 80), rng.randint(-190, -110)
            r = rng.randint(14, 26) * s
            cx, cy = P(px, py)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#5b5560", outline="")


def draw_sea_battle(c):
    """Startbild: Seeschlacht bei Sonnenuntergang."""
    rng = random.Random(11)
    draw_gradient(c, 0, 0, WIDTH, 250, "#241a45", "#8a3f5a")
    draw_gradient(c, 0, 250, WIDTH, 400, "#8a3f5a", "#f4b062")
    for r, col in ((130, "#f7b873"), (90, "#fbd08f"), (58, "#ffe7b8")):
        c.create_oval(550 - r, 400 - r, 550 + r, 400 + r, fill=col, outline="")
    for _ in range(7):
        x, y = rng.randint(0, WIDTH), rng.randint(110, 240)
        c.create_oval(x - 120, y - 16, x + 120, y + 16, fill="#4a2c4f", outline="")
    draw_gradient(c, 0, 400, WIDTH, HEIGHT, "#2c6180", "#06131e")
    for i in range(24):
        y = 404 + i * 4
        half = 90 - i * 3
        if half > 8:
            c.create_line(550 - half, y, 550 + half, y, fill="#ffd9a0", width=2)
    for _ in range(170):
        x, y = rng.randint(0, WIDTH), rng.randint(406, HEIGHT)
        w = rng.randint(14, 60)
        c.create_line(x, y, x + w, y, fill=mix("#6aa6c4", "#10304a", (y - 400) / 300))

    red, blue, spain = "#cf142b", "#0055a4", "#c60b1e"
    far = [(560, 428, 0.42, 1, "#d9cdb0", "#cf142b", True),
           (80, 462, 0.55, 1, "#efe3c2", red, False),
           (1030, 458, 0.55, -1, "#efe3c2", blue, False),
           (330, 505, 0.78, 1, "#efe3c2", red, False),
           (775, 505, 0.78, -1, "#efe3c2", spain, False)]
    near = [(170, 585, 1.05, 1, "#f6ecd0", red, False),
            (940, 590, 1.05, -1, "#f6ecd0", blue, False)]
    for sx, sy, s, face, sail, flag, burn in far:
        draw_tall_ship(c, sx, sy, s, face, sail, flag, burn, rng)
    for _ in range(26):
        x, y = rng.randint(300, 800), rng.randint(405, 540)
        r = rng.randint(12, 30)
        c.create_oval(x - r, y - r, x + r, y + r,
                      fill=rng.choice(["#8d8794", "#a59fa8", "#6f6a76"]), outline="")
    for sx, sy, s, face, sail, flag, burn in near:
        draw_tall_ship(c, sx, sy, s, face, sail, flag, burn, rng)
    for sx, sy, s, face in [(330, 505, 0.78, 1), (775, 505, 0.78, -1),
                            (170, 585, 1.05, 1), (940, 590, 1.05, -1)]:
        fx, fy = sx + face * 128 * s, sy - 6 * s
        for r, col in ((22 * s, "#ff9d2e"), (13 * s, "#fff1a8")):
            c.create_oval(fx - r, fy - r, fx + r, fy + r, fill=col, outline="")


def draw_planks(c):
    rng = random.Random(5)
    y, i = 0, 0
    while y < HEIGHT:
        c.create_rectangle(0, y, WIDTH, y + 44, fill="#4f3320" if i % 2 == 0 else "#5a3a24",
                           outline="#2a1a10")
        x = rng.randint(0, 200)
        while x < WIDTH:
            c.create_line(x, y, x, y + 44, fill="#2a1a10")
            x += rng.randint(220, 380)
        for _ in range(4):
            gx = rng.randint(0, WIDTH)
            c.create_line(gx, y + rng.randint(8, 36), gx + rng.randint(40, 120), y + rng.randint(8, 36),
                          fill="#3d2616")
        y += 44
        i += 1


def draw_cannon(c, x, y, facing):
    def X(px):
        return x + facing * px
    c.create_polygon(X(-70), y + 4, X(-20), y + 40, X(50), y + 40, X(60), y + 4,
                     fill="#6b4524", outline="#1a0f08", width=2)
    c.create_polygon(X(-62), y - 16, X(52), y - 11, X(52), y + 9, X(-62), y + 14,
                     fill="#1b1612", outline="#000000", width=2)
    c.create_rectangle(min(X(48), X(62)), y - 16, max(X(48), X(62)), y + 11,
                       fill="#2b241e", outline="#000000", width=2)
    c.create_rectangle(min(X(-66), X(-58)), y - 6, max(X(-66), X(-58)), y + 6,
                       fill="#2b241e", outline="#000000")
    for wx in (-35, 35):
        c.create_oval(X(wx) - 17, y + 28, X(wx) + 17, y + 62, fill="#5a3a1e", outline="#0d0805", width=3)
        c.create_oval(X(wx) - 5, y + 40, X(wx) + 5, y + 50, fill="#1a0f08", outline="")


def draw_porthole(c, x, y, r):
    c.create_oval(x - r - 10, y - r - 10, x + r + 10, y + r + 10, fill="#7a5a2a", outline="#2a1a10", width=3)
    c.create_oval(x - r, y - r, x + r, y + r, fill="#4f94b8", outline="#2a1a10", width=3)
    c.create_oval(x - r + 6, y - r + 6, x + r - 6, y - 2, fill="#8cc4dc", outline="")
    for i in range(3):
        c.create_line(x - r + 12, y + 8 + i * 9, x + r - 12, y + 8 + i * 9, fill="#d6eef7")
    for ang in range(0, 360, 60):
        bx = x + (r + 10) * (1 if ang in (0, 60, 300) else -1)
        c.create_oval(bx - 3, y - 3, bx + 3, y + 3, fill="#3d2a12", outline="")


def draw_lantern(c, x, y):
    c.create_line(x, 0, x, y - 22, fill="#2a1a10", width=3)
    c.create_oval(x - 46, y - 40, x + 46, y + 48, fill="#6e4a26", outline="")
    c.create_oval(x - 30, y - 26, x + 30, y + 34, fill="#9a6a30", outline="")
    c.create_rectangle(x - 14, y - 18, x + 14, y + 24, fill="#f6c76a", outline="#2a1a10", width=3)
    c.create_polygon(x - 20, y - 18, x + 20, y - 18, x, y - 34, fill="#2a1a10", outline="")


def draw_interior(c):
    """Setup-Bild: Inneres eines Kriegsschiffs (Kanonendeck)."""
    draw_planks(c)
    c.create_rectangle(0, 0, 46, HEIGHT, fill="#2e1c10", outline="#150c06", width=3)
    c.create_rectangle(WIDTH - 46, 0, WIDTH, HEIGHT, fill="#2e1c10", outline="#150c06", width=3)
    c.create_rectangle(0, 0, WIDTH, 22, fill="#2e1c10", outline="#150c06", width=3)
    c.create_rectangle(0, HEIGHT - 28, WIDTH, HEIGHT, fill="#2e1c10", outline="#150c06", width=3)
    draw_porthole(c, 150, 240, 42)
    draw_porthole(c, 950, 240, 42)
    draw_lantern(c, 150, 90)
    draw_lantern(c, 950, 90)
    draw_cannon(c, 150, 560, 1)
    draw_cannon(c, 950, 560, -1)
    for x in (110, 190, 910, 990):
        c.create_oval(x - 11, 372 - 11, x + 11, 372 + 11, fill="#16110d", outline="#000000", width=2)


def make_waves(count=120):
    rng = random.Random(21)
    return [(rng.randint(0, WIDTH), rng.randint(0, HEIGHT), rng.randint(14, 50)) for _ in range(count)]


WAVES = make_waves()


def draw_battle_background(c):
    draw_gradient(c, 0, 0, WIDTH, HEIGHT, "#17506b", "#071a28", 30)
    for x, y, w in WAVES:
        c.create_line(x, y, x + w, y, fill=mix("#3f8aa8", "#0d2a40", y / HEIGHT))


def draw_ship_shape(c, ship, x0, y0, cell, nation):
    """Zeichnet ein Schiff als Rumpf mit Mast-Markierungen ueber seinen Kaestchen."""
    rows = [r for r, _ in ship["cells"]]
    cols = [col for _, col in ship["cells"]]
    left, top = x0 + min(cols) * cell, y0 + min(rows) * cell
    horizontal = len(set(rows)) == 1
    length = ship["size"] * cell
    pad = 5
    bow = cell * 0.35

    def M(u, v):
        return (left + u, top + v) if horizontal else (left + v, top + u)

    outline = [(pad, pad + 2), (length - bow, pad + 2), (length - pad + 2, cell / 2),
               (length - bow, cell - pad - 2), (pad, cell - pad - 2)]
    pts = []
    for u, v in outline:
        pts.extend(M(u, v))
    hull = "#8a6d1f" if ship["kind"] == "treasure" else "#3b2a1a"
    c.create_polygon(pts, fill=hull, outline="#120a05", width=2)
    a, b = M(pad + 4, cell / 2), M(length - bow - 2, cell / 2)
    c.create_line(a[0], a[1], b[0], b[1], fill=NATION_COLORS[nation][0], width=3)
    for i in range(ship["size"]):
        u = (i + 0.5) * cell
        a, b = M(u, pad + 5), M(u, cell - pad - 5)
        c.create_line(a[0], a[1], b[0], b[1], fill="#efe3c2", width=4)
        m = M(u, cell / 2)
        c.create_oval(m[0] - 3, m[1] - 3, m[0] + 3, m[1] + 3, fill="#1a0f08", outline="")


def draw_skull(c, cx, cy, s):
    """Kleiner Totenkopf: Schaedel, Augen, Nase und Zaehne (Kennzeichen fuer versenkte Schiffe)."""
    bone, dark = "#f4ecd2", "#1a0f08"
    c.create_oval(cx - s, cy - s * 1.05, cx + s, cy + s * 0.55, fill=bone, outline=dark, width=2)
    c.create_rectangle(cx - s * 0.55, cy + s * 0.35, cx + s * 0.55, cy + s, fill=bone, outline=dark, width=2)
    for dx in (-0.4, 0.4):
        c.create_oval(cx + dx * s - s * 0.28, cy - s * 0.45, cx + dx * s + s * 0.28, cy + s * 0.1,
                      fill=dark, outline="")
    c.create_polygon(cx, cy + s * 0.05, cx - s * 0.12, cy + s * 0.32, cx + s * 0.12, cy + s * 0.32,
                     fill=dark, outline="")
    for dx in (-0.25, 0, 0.25):
        c.create_line(cx + dx * s, cy + s * 0.6, cx + dx * s, cy + s * 0.98, fill=dark)


def draw_board(c, board, x0, y0, cell, show_ships=False, nation="England", show_scouted=False):
    """Zeichnet ein Spielfeld im Stil einer Seekarte."""
    size = GRID * cell
    c.create_rectangle(x0 - 10, y0 - 10, x0 + size + 10, y0 + size + 10,
                       fill="#4a2f18", outline="#1f1208", width=3)
    for i in range(GRID):
        c.create_text(x0 + i * cell + cell / 2, y0 - 20, text=LETTERS[i],
                      font=(FONT, 11, "bold"), fill=GOLD)
        c.create_text(x0 - 22, y0 + i * cell + cell / 2, text=str(i + 1),
                      font=(FONT, 11, "bold"), fill=GOLD)
    for r in range(GRID):
        for col in range(GRID):
            res = board["shots"].get((r, col))
            fill = {"miss": MISS_BLUE, "hit": HIT_RED, "treasure": TREASURE_GOLD}.get(res, SEA_CHART)
            c.create_rectangle(x0 + col * cell, y0 + r * cell,
                               x0 + (col + 1) * cell, y0 + (r + 1) * cell,
                               fill=fill, outline=CHART_LINE)
    if show_ships:
        for ship in board["ships"]:
            draw_ship_shape(c, ship, x0, y0, cell, nation)
    for (r, col), res in board["shots"].items():
        xa, ya = x0 + col * cell, y0 + r * cell
        if res == "miss":
            continue
        ship = ship_at(board, (r, col))
        if res == "hit" and ship is not None and is_sunk(ship):
            draw_skull(c, xa + cell / 2, ya + cell / 2, cell * 0.3)   # versenktes Schiff
        elif show_ships:
            m = cell * 0.27
            cx, cy = xa + cell / 2, ya + cell / 2
            c.create_oval(cx - m, cy - m, cx + m, cy + m,
                          fill=HIT_RED if res == "hit" else TREASURE_GOLD,
                          outline="#1a0f08", width=2)
        else:
            c.create_line(xa + 8, ya + 8, xa + cell - 8, ya + cell - 8, fill="#4a0d08", width=3)
            c.create_line(xa + cell - 8, ya + 8, xa + 8, ya + cell - 8, fill="#4a0d08", width=3)
    for ship in board["ships"]:
        if is_sunk(ship) and ship["kind"] != "treasure":
            rows = [r for r, _ in ship["cells"]]
            cols = [col for _, col in ship["cells"]]
            c.create_rectangle(x0 + min(cols) * cell + 2, y0 + min(rows) * cell + 2,
                               x0 + (max(cols) + 1) * cell - 2, y0 + (max(rows) + 1) * cell - 2,
                               outline="#120a05", width=3)
    if show_scouted:
        for (r, col), has in board["scouted"].items():
            if (r, col) in board["shots"]:
                continue
            cx, cy = x0 + col * cell + cell / 2, y0 + r * cell + cell / 2
            if has:
                d = cell * 0.28
                c.create_polygon(cx, cy - d, cx + d, cy, cx, cy + d, cx - d, cy,
                                 fill="#5a1010", outline="#f4e3b3", width=2)
            else:
                d = cell * 0.12
                c.create_oval(cx - d, cy - d, cx + d, cy + d, fill="#f3ead0", outline="#9c8454")


def cell_at(x, y, x0, y0, cell):
    col, row = int((x - x0) // cell), int((y - y0) // cell)
    if 0 <= row < GRID and 0 <= col < GRID and x >= x0 and y >= y0:
        return (row, col)
    return None


def draw_prize_icon(c, prize, cx, cy):
    """Zeichnet das Symbol eines Truhenpreises (Mitte bei cx, cy)."""
    def ball(x, y, r=11):
        c.create_oval(x - r, y - r, x + r, y + r, fill="#222222", outline="#000000", width=2)
        c.create_oval(x - r * 0.55, y - r * 0.6, x - r * 0.1, y - r * 0.15, fill="#777777", outline="")

    if prize == "reinforcement":
        c.create_polygon(cx - 30, cy + 10, cx + 30, cy + 10, cx + 20, cy + 26, cx - 20, cy + 26,
                         fill="#3b2a1a", outline="#1a0f08", width=2)
        c.create_line(cx, cy + 10, cx, cy - 30, fill="#1a0f08", width=3)
        c.create_polygon(cx, cy - 26, cx + 30, cy + 6, cx, cy + 6, fill="#efe3c2", outline="#8a7a55")
    elif prize == "broadside":
        for dx in (-30, 0, 30):
            ball(cx + dx, cy + 8)
    elif prize == "mortar":
        for dx in (-14, 14):
            for dy in (-8, 16):
                ball(cx + dx, cy + dy)
    elif prize == "gunners":
        ball(cx - 12, cy + 8, 16)
        c.create_text(cx + 30, cy + 8, text="+1", font=(FONT, 22, "bold"), fill="#8b1a1a")
    elif prize == "signals":
        c.create_line(cx - 28, cy + 22, cx + 22, cy - 12, fill="#7a5a2a", width=10)
        c.create_oval(cx + 18, cy - 26, cx + 44, cy, outline="#d9a441", width=5, fill="#bfe6f5")
    elif prize == "fireship":
        c.create_polygon(cx - 30, cy + 14, cx + 30, cy + 14, cx + 20, cy + 28, cx - 20, cy + 28,
                         fill="#3b2a1a", outline="#1a0f08", width=2)
        for dx, h in ((-18, 40), (2, 52), (22, 36)):
            c.create_polygon(cx + dx - 11, cy + 14, cx + dx, cy + 14 - h, cx + dx + 11, cy + 14,
                             fill="#e8590c", outline="")
            c.create_polygon(cx + dx - 5, cy + 14, cx + dx, cy + 14 - h * 0.55, cx + dx + 5, cy + 14,
                             fill="#ffd23f", outline="")
    elif prize == "gold":
        for i in range(3):
            y = cy + 16 - i * 10
            c.create_oval(cx - 30, y - 8, cx + 8, y + 8, fill="#f2b705", outline="#7a5a00", width=2)
        c.create_text(cx + 32, cy, text="+5", font=(FONT, 22, "bold"), fill="#8a6d1f")
    elif prize == "repair":
        c.create_line(cx - 22, cy + 26, cx + 8, cy - 8, fill="#7a4a1e", width=9)
        c.create_rectangle(cx - 6, cy - 28, cx + 30, cy - 8, fill="#8a8a8a", outline="#1a0f08", width=2)
    else:   # "map"
        c.create_oval(cx - 42, cy - 26, cx - 28, cy + 26, fill="#c4a76a", outline="#5a3a1e", width=2)
        c.create_oval(cx + 28, cy - 26, cx + 42, cy + 26, fill="#c4a76a", outline="#5a3a1e", width=2)
        c.create_rectangle(cx - 35, cy - 24, cx + 35, cy + 24, fill="#d9c08a", outline="#5a3a1e", width=2)
        c.create_line(cx - 24, cy + 12, cx - 10, cy - 8, cx + 4, cy + 6, dash=(4, 3), fill="#5a3a1e", width=2)
        c.create_line(cx + 8, cy - 10, cx + 24, cy + 6, fill="#b3261e", width=4)
        c.create_line(cx + 24, cy - 10, cx + 8, cy + 6, fill="#b3261e", width=4)


# ======================================================================
# 6. OBERFLAECHE
# ======================================================================
def opp(who):
    """Der Gegner von p1 ist p2 und umgekehrt."""
    return "p2" if who == "p1" else "p1"


def short(name, n=9):
    return name if len(name) <= n else name[:n - 1] + "."


# ======================================================================
# KLAENGE (optional): liegen als .wav im Ordner "sounds" neben dieser Datei.
# Fehlt der Ordner oder gibt es keinen Abspieler, laeuft das Spiel einfach ohne Ton.
# ======================================================================
SOUND_FILES = {k: k + ".wav" for k in (
    "kanonenschuss", "treffer", "fehlschuss", "schatzschiff", "versenkt", "sieg", "niederlage",
    "captains_quarters", "segel_setzen", "england", "frankreich", "spanien", "klick", "retreat",
    "start_meer", "join_trommel", "papier", "new_entrant", "lieutenant_commander", "admiral",
    "federkratzen", "schiff_setzen", "schiff_drehen", "ungueltig", "random", "reset", "open_fire",
    "muenzwurf", "truhe", "computer_denkt", "uebergabe")}
SHOT_FLIGHT_MS = 1100      # Flugzeit der Kugel: so lange nach dem Schuss kommt das Ergebnis


class Sounds:
    def __init__(self, enabled=True):
        self.enabled = enabled
        base = os.path.dirname(os.path.abspath(__file__))
        self.paths = {}
        for key, name in SOUND_FILES.items():
            path = os.path.join(base, "sounds", name)
            if os.path.isfile(path):
                self.paths[key] = path
        self.procs = {}
        self.player = None
        if sys.platform == "darwin":
            self.player = shutil.which("afplay")
        elif sys.platform.startswith("win"):
            self.player = "winsound"
        else:
            self.player = shutil.which("paplay") or shutil.which("aplay")

    @property
    def available(self):
        return bool(self.paths) and bool(self.player)

    def play(self, key, channel=None):
        """Spielt einen Klang. Mit 'channel' wird ein dort noch laufender Klang vorher abgebrochen."""
        if not (self.enabled and self.available) or key not in self.paths:
            return
        if channel:
            self.stop(channel)
        path = self.paths[key]
        try:
            if self.player == "winsound":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                proc = subprocess.Popen([self.player, path], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                if channel:
                    self.procs[channel] = proc
        except Exception:
            pass

    def stop(self, channel):
        proc = self.procs.pop(channel, None)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def stop_all(self):
        for ch in list(self.procs):
            self.stop(ch)


class TrafalgarApp:
    def __init__(self, root):
        self.root = root
        root.title("Battle of Trafalgar")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0, bg="#10202e")
        self.canvas.pack()

        self.data = load_data()
        self.sound = Sounds(self.data.get("sound", True))
        self.name_var = tk.StringVar(value=self.data["last_name"])
        self.mode = self.data["last_mode"] if self.data["last_mode"] in ("ai", "pvp") else "ai"
        self.difficulty = (self.data["last_difficulty"]
                           if self.data["last_difficulty"] in DIFFICULTIES else "New Entrant")
        self.sel_nation = self.data["last_nation"] if self.data["last_nation"] in NATIONS else "England"
        self.setup = {}
        self.setup_step = 1
        self.P = {}                       # die beiden Parteien p1 und p2
        self.viewer = "p1"                # wessen Sicht gerade am Bildschirm ist
        self.turn = "p1"
        self.placing = "p1"
        self.sel = 0
        self.horizontal = True
        self.special = {"p1": None, "p2": None}     # geladener Spezialschuss
        self.skip = {"p1": False, "p2": False}      # naechsten Zug aussetzen (Fireship)
        self.log = []
        self.reveal = False
        self.shots_left = 1
        self.banner_msg = None
        self.inventory = {"p1": [], "p2": []}       # gelagerte Preise (Laderaum)
        self.turn_no = 0                            # zaehlt jeden Zug, steuert "ab der naechsten Runde"
        self.entry = None
        self.images = {}
        self.screen = "start"
        self.session = 0
        self._btn_time = -1
        self._bg_job = None
        self.snd_pos = (1010, 38)
        self.hover = None
        self.overlay = None
        self.phase = ""

        c = self.canvas
        c.bind("<Button-1>", self.on_left)
        c.bind("<Button-3>", self.on_right)
        c.bind("<Button-2>", self.on_right)
        c.bind("<Control-Button-1>", self.on_right)
        c.bind("<Motion>", self.on_motion)
        root.bind("<KeyPress-r>", self.on_rotate_key)
        root.bind("<KeyPress-R>", self.on_rotate_key)

        self.show_start()
        root.after(300, self.refresh_start)

    # ---------------- Hilfsfunktionen ----------------
    def refresh_start(self):
        """Zeichnet den Startbildschirm kurz nach dem Oeffnen des Fensters noch einmal."""
        if self.screen == "start":
            self.show_start()

    def clear(self):
        if self.entry is not None:
            self.entry.destroy()
            self.entry = None
        self.canvas.delete("all")
        self.canvas.config(cursor="")

    def later(self, ms, fn):
        """after() mit Schutz: Callback verfaellt, wenn inzwischen ein neues Spiel/Bild aktiv ist."""
        token = self.session
        self.root.after(ms, lambda: fn() if token == self.session else None)

    def load_image(self, filename):
        path = os.path.join(ASSET_DIR, filename)
        if not os.path.exists(path):
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGB").resize((WIDTH, HEIGHT))
            photo = ImageTk.PhotoImage(img)
        except ImportError:
            try:
                photo = tk.PhotoImage(file=path)
            except tk.TclError:
                return None
        except Exception:
            return None
        self.images[filename] = photo
        return photo

    def mark(self, event):
        self._btn_time = event.time

    OWN_SOUND_TAGS = {"btn_join", "btn_sail", "btn_rot", "btn_rnd", "btn_reset", "btn_fire", "btn_retreat"}

    def bind_click(self, tag, func):
        self.canvas.tag_bind(tag, "<Button-1>", lambda e: (self.mark(e), func()))

    def button(self, cx, cy, w, h, text, command, tag, size=18, enabled=True):
        c = self.canvas
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        base = "#7a5230" if enabled else "#6b6b6b"
        c.create_rectangle(x0 + 3, y0 + 4, x1 + 3, y1 + 4, fill="#120a05", outline="", tags=(tag,))
        rect = c.create_rectangle(x0, y0, x1, y1, fill=base, outline=GOLD if enabled else "#999999",
                                  width=3, tags=(tag,))
        c.create_text(cx, cy, text=text, font=(FONT, size, "bold"),
                      fill="#fbeecb" if enabled else "#cccccc", tags=(tag,))
        if enabled:
            def clicked(command=command, tag=tag):
                if tag not in self.OWN_SOUND_TAGS:
                    self.sound.play("klick")
                command()
            self.bind_click(tag, clicked)
            c.tag_bind(tag, "<Enter>", lambda e: (c.itemconfig(rect, fill="#9a6a3c"), c.config(cursor="hand2")))
            c.tag_bind(tag, "<Leave>", lambda e: (c.itemconfig(rect, fill=base), c.config(cursor="")))

    def sound_button(self, cx=1010, cy=38):
        self.snd_pos = (cx, cy)
        if self.sound.available:
            self.button(cx, cy, 100, 34, "Sound: %s" % ("On" if self.sound.enabled else "Off"),
                        self.toggle_sound, "btn_sound", size=11)

    def start_bg(self):
        """Meeresrauschen mit fernen Kanonen auf dem Startbildschirm; wiederholt sich alle 10 s."""
        if self._bg_job:
            self.root.after_cancel(self._bg_job)
            self._bg_job = None
        if self.screen != "start":
            return
        self.sound.play("start_meer", "bg")
        self._bg_job = self.root.after(10000, self.start_bg)

    def stop_bg(self):
        if self._bg_job:
            self.root.after_cancel(self._bg_job)
            self._bg_job = None
        self.sound.stop("bg")

    def option_box(self, cx, cy, w, h, label, selected, tags, size=12):
        self.canvas.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2,
                                     fill="#7a5230" if selected else "#cdb98a",
                                     outline="#c9a227" if selected else "#6b4a22",
                                     width=4 if selected else 2, tags=tags)
        self.canvas.create_text(cx, cy, text=label, font=(FONT, size, "bold"),
                                fill="#fbeecb" if selected else INK, tags=tags)

    def shadow_text(self, x, y, text, size, color=GOLD, style="bold"):
        self.canvas.create_text(x + 3, y + 3, text=text, font=(FONT, size, style), fill="#120a05")
        self.canvas.create_text(x, y, text=text, font=(FONT, size, style), fill=color)

    # Namen fuer Meldungen: gegen den Computer "You"/"The enemy", gegen einen Menschen die Namen
    def actor(self, who):
        if self.mode == "ai":
            return "You" if who == "p1" else "The enemy"
        return self.P[who]["name"]

    def owner(self, who):
        if self.mode == "ai":
            return "your" if who == "p1" else "the enemy's"
        return self.P[who]["name"] + "'s"

    def say(self, text):
        self.log.append(text)
        self.log = self.log[-4:]

    # ---------------- Startbildschirm ----------------
    def show_start(self):
        self.session += 1
        self.stop_bg()
        self.screen = "start"
        self.overlay = None
        self.clear()
        bg = self.load_image("start.png")
        if bg:
            self.canvas.create_image(0, 0, image=bg, anchor="nw")
        else:
            draw_sea_battle(self.canvas)
        self.shadow_text(WIDTH / 2, 95, "BATTLE OF TRAFALGAR", 46)
        self.shadow_text(WIDTH / 2, 148, "Cape Trafalgar, 21 October 1805", 18, "#f6e7c1", "italic")
        self.button(WIDTH / 2, HEIGHT / 2, 320, 76, "Join the Fleet", self.join_fleet, "btn_join", size=26)
        self.draw_hall_of_fame()
        self.sound_button(1010, 38)
        self.start_bg()

    def join_fleet(self):
        self.stop_bg()
        self.sound.play("join_trommel")
        self.show_intro()

    def draw_hall_of_fame(self):
        players = sorted(self.data["players"].items(), key=lambda kv: -kv[1]["total"])[:3]
        if not players:
            return
        c = self.canvas
        c.create_rectangle(18, HEIGHT - 28 - 26 * len(players) - 34, 318, HEIGHT - 16,
                           fill="#120a05", outline=GOLD, width=2)
        y = HEIGHT - 28 - 26 * len(players) - 14
        c.create_text(168, y, text="Hall of Fame", font=(FONT, 14, "bold italic"), fill=GOLD)
        for i, (name, rec) in enumerate(players):
            c.create_text(32, y + 26 * (i + 1), anchor="w",
                          text="%d. %s" % (i + 1, name[:16]), font=(FONT, 13), fill="#f6e7c1")
            c.create_text(304, y + 26 * (i + 1), anchor="e",
                          text="%d pts" % rec["total"], font=(FONT, 13, "bold"), fill=GOLD)

    # ---------------- Einfuehrungsseite ----------------
    def show_intro(self):
        self.session += 1
        self.screen = "intro"
        self.overlay = None
        self.clear()
        c = self.canvas
        draw_planks(c)
        self.shadow_text(550, 34, "Briefing for the Fleet", 28)
        draw_parchment(c, 40, 62, 1060, 662)
        # --- Nationen ---
        c.create_text(550, 84, text="Die drei Nationen", font=(FONT, 15, "bold italic"), fill=INK)
        for i, nation in enumerate(NATIONS):
            x = 60 + i * 335
            draw_flag(c, nation, x, 104, 48, 32)
            c.create_rectangle(x, 104, x + 48, 136, outline="#2a1a10", width=2)
            names = {"Spain": "Spanien", "France": "Frankreich", "England": "England"}
            c.create_text(x + 60, 120, anchor="w", text=names[nation], font=(FONT, 14, "bold"), fill=INK)
            c.create_text(x, 146, anchor="nw", width=310, font=(FONT, 11), fill=INK,
                          text=INTRO_NATIONS_DE[nation])
        c.create_line(60, 226, 1040, 226, fill="#b89a5a")
        # --- Schwierigkeitsgrade ---
        c.create_text(550, 243, text="Die Schwierigkeitsgrade", font=(FONT, 15, "bold italic"), fill=INK)
        for i, (name, text) in enumerate(INTRO_LEVELS_DE):
            x = 60 + i * 335
            c.create_text(x, 265, anchor="nw", text=name, font=(FONT, 12, "bold"), fill="#8b1a1a")
            c.create_text(x, 284, anchor="nw", width=310, font=(FONT, 11), fill=INK, text=text)
        c.create_line(60, 345, 1040, 345, fill="#b89a5a")
        # --- Spielanleitung ---
        c.create_text(550, 363, text="Spielanleitung", font=(FONT, 15, "bold italic"), fill=INK)
        y = 384
        for i, step in enumerate(INTRO_STEPS_DE, 1):
            c.create_text(62, y, anchor="nw", text="%d." % i, font=(FONT, 10, "bold"), fill="#8b1a1a")
            t = c.create_text(88, y, anchor="nw", width=940, font=(FONT, 10), fill=INK, text=step)
            box = c.bbox(t)
            y = box[3] + 4
        self.button(550, 636, 380, 38, "Next: The Treasure Chest", self.show_prizes, "btn_intro_next", size=15)
        self.button(110, 636, 120, 32, "Back", self.show_start, "btn_intro_back", size=12)
        self.sound_button(1010, 34)
        self.sound.play("papier")

    def show_prizes(self):
        """Zweite Einfuehrungsseite: Was die Preise der Schatztruhe bewirken."""
        self.session += 1
        self.screen = "intro"
        self.overlay = None
        self.clear()
        c = self.canvas
        draw_planks(c)
        self.shadow_text(550, 34, "Briefing: The Treasure Chest", 28)
        draw_parchment(c, 40, 62, 1060, 662)
        c.create_text(550, 134, width=980, justify="center", font=(FONT, 13), fill=INK, text=PRIZE_INTRO_DE)
        c.create_line(60, 186, 1040, 186, fill="#b89a5a")
        names = {"Spain": "Spanien", "France": "Frankreich", "England": "England"}
        for i, nation in enumerate(NATIONS):
            x = 70 + i * 335
            draw_flag(c, nation, x, 204, 56, 38)
            c.create_rectangle(x, 204, x + 56, 242, outline="#2a1a10", width=2)
            c.create_text(x + 70, 223, anchor="w", text=names[nation], font=(FONT, 17, "bold"), fill=INK)
            for k, prize in enumerate(NATION_PRIZES[nation]):
                title, text = PRIZE_TEXT_DE[prize]
                y = 270 + k * 118
                c.create_text(x, y, anchor="nw", text=title, font=(FONT, 14, "bold"), fill="#8b1a1a")
                c.create_text(x, y + 26, anchor="nw", width=310, font=(FONT, 12), fill=INK, text=text)
                if k < 2:
                    c.create_line(x, y + 110, x + 300, y + 110, fill="#d2bf8c")
        self.button(550, 636, 340, 38, "To the Captain's Quarters", self.show_setup, "btn_prize_next", size=15)
        self.button(110, 636, 120, 32, "Back", self.show_intro, "btn_prize_back", size=12)
        self.sound_button(1010, 34)
        self.sound.play("papier")

    # ---------------- Setup: Name, Gegner, Schwierigkeit, Nation ----------------
    def show_setup(self, step=1, keep=False):
        self.session += 1
        self.screen = "setup"
        self.setup_step = step
        self.clear()
        bg = self.load_image("interior.png")
        if bg:
            self.canvas.create_image(0, 0, image=bg, anchor="nw")
        else:
            draw_interior(self.canvas)
        c = self.canvas
        draw_parchment(c, 250, 55, 850, 665)
        if step == 1:
            self.name_var.set(self.data["last_name"])
            if keep and self.setup.get("p1"):
                self.sel_nation = self.setup["p1"]["nation"]
            title, sub, label = ("Captain's Quarters", "Sign the muster roll before you set sail", "Your name")
        else:
            self.name_var.set(self.data.get("last_name2", ""))
            p1_nation = self.setup["p1"]["nation"]
            self.sel_nation = [n for n in NATIONS if n != p1_nation][0]
            if keep and self.setup.get("p2") and self.setup["p2"]["nation"] != p1_nation:
                self.sel_nation = self.setup["p2"]["nation"]
            title, sub, label = ("Second Captain", "Pass the computer to the second captain",
                                 "Name of the second captain")
        c.create_text(550, 92, text=title, font=(FONT, 28, "bold italic"), fill=INK)
        c.create_text(550, 124, text=sub, font=(FONT, 13, "italic"), fill=INK)
        c.create_text(550, 160, text=label, font=(FONT, 15, "bold"), fill=INK)
        self.entry = tk.Entry(self.root, textvariable=self.name_var, font=(FONT, 16), justify="center",
                              width=24, bg="#fbf3d9", fg=INK, relief="solid", bd=2)
        c.create_window(550, 196, window=self.entry)
        self.entry.focus_set()
        self._quill_done = False
        self.entry.bind("<Button-1>", self.quill)
        self.sound.play("captains_quarters", "scene")
        self.sound_button(1010, 38)
        c.create_text(550, 429, text="Nation", font=(FONT, 16, "bold"), fill=INK)
        self.draw_setup_options()
        self.button(550, 622, 260, 54, "Setting Sails", self.setup_done, "btn_sail", size=22)

    def draw_setup_options(self):
        c = self.canvas
        c.delete("opt")
        if self.setup_step == 1:
            c.create_text(550, 238, text="Opponent", font=(FONT, 15, "bold"), fill=INK, tags=("opt",))
            for i, (key, label) in enumerate((("ai", "Computer"), ("pvp", "Second Player"))):
                tag = "mode%d" % i
                self.option_box(455 + i * 190, 274, 170, 40, label, key == self.mode, ("opt", tag), 12)
                self.bind_click(tag, lambda k=key: self.select_mode(k))
            if self.mode == "ai":
                descs = {"New Entrant": "The enemy fires blindly into the fog.",
                         "Lieutenant-Commander": "The enemy hunts down your wounded ships.",
                         "Admiral": "The enemy calculates every single shot."}
                c.create_text(550, 322, text="Difficulty", font=(FONT, 15, "bold"), fill=INK, tags=("opt",))
                for i, name in enumerate(DIFFICULTIES):
                    tag = "diff%d" % i
                    self.option_box(365 + i * 185, 358, 176, 44, name, name == self.difficulty,
                                    ("opt", tag), 10)
                    self.bind_click(tag, lambda n=name: self.select_difficulty(n))
                c.create_text(550, 396, text=descs[self.difficulty], font=(FONT, 12, "italic"),
                              fill=INK, tags=("opt",))
            else:
                c.create_text(550, 358, justify="center", font=(FONT, 13, "italic"), fill=INK,
                              text="Two captains share one computer.\nThe screen is hidden whenever the turn changes.",
                              tags=("opt",))
        else:
            c.create_text(550, 300, justify="center", font=(FONT, 14, "italic"), fill=INK,
                          text="Captain %s has signed the roll.\nNow it is your turn!" % self.setup["p1"]["name"],
                          tags=("opt",))
        for i, nation in enumerate(NATIONS):
            cx = 400 + i * 150
            x0, y0 = cx - 45, 458
            tag = "nat%d" % i
            if nation == self.sel_nation:
                c.create_rectangle(x0 - 9, y0 - 9, x0 + 99, y0 + 69, fill="#c9a227",
                                   outline="#5a3a1e", width=2, tags=("opt", tag))
            draw_flag(c, nation, x0, y0, 90, 60, tags=("opt", tag))
            c.create_text(cx, 541, text=nation, font=(FONT, 14, "bold"), fill=INK, tags=("opt", tag))
            self.bind_click(tag, lambda n=nation: self.select_nation(n))
        c.create_text(550, 575, justify="center", font=(FONT, 11, "italic"), fill=INK,
                      text=NATION_INFO_DE[self.sel_nation], tags=("opt",))

    def quill(self, event=None):
        if not self._quill_done:
            self._quill_done = True
            self.sound.play("federkratzen", "quill")

    def select_mode(self, key):
        self.sound.play("klick")
        self.mode = key
        self.draw_setup_options()

    def select_difficulty(self, name):
        self.difficulty = name
        self.sound.play({"New Entrant": "new_entrant", "Lieutenant-Commander": "lieutenant_commander",
                         "Admiral": "admiral"}[name], "diff")
        self.draw_setup_options()

    def select_nation(self, name):
        self.sel_nation = name
        self.sound.play({"Spain": "spanien", "France": "frankreich", "England": "england"}[name], "nation")
        self.draw_setup_options()

    def setup_done(self):
        name = self.name_var.get().strip()[:20]
        self.canvas.delete("err")
        error = None
        if not name:
            error = "Please enter your name, Captain!"
        elif self.setup_step == 2 and name.lower() == self.setup["p1"]["name"].lower():
            error = "Please choose a different name from the first captain."
        if error:
            self.canvas.create_text(550, 411, text=error, font=(FONT, 14, "bold italic"),
                                    fill="#8b1a1a", tags=("err",))
            self.sound.play("ungueltig")
            return
        for ch in ("nation", "diff", "scene", "quill"):
            self.sound.stop(ch)
        self.sound.play("segel_setzen", "scene")
        if self.setup_step == 1:
            self.setup = {"p1": {"name": name, "nation": self.sel_nation, "ai": False}}
            self.data.update({"last_name": name, "last_nation": self.sel_nation,
                              "last_difficulty": self.difficulty, "last_mode": self.mode})
            save_data(self.data)
            if self.mode == "pvp":
                self.show_setup(step=2)
                return
            enemy_nation = random.choice([n for n in NATIONS if n != self.sel_nation])
            self.setup["p2"] = {"name": COMMANDERS[enemy_nation], "nation": enemy_nation, "ai": True}
        else:
            self.setup["p2"] = {"name": name, "nation": self.sel_nation, "ai": False}
            self.data["last_name2"] = name
            save_data(self.data)
        self.begin_placement()

    def begin_placement(self):
        self.P = {}
        for who in ("p1", "p2"):
            s = self.setup[who]
            self.P[who] = {"name": s["name"], "nation": s["nation"], "ai": s["ai"], "points": 0,
                           "board": new_board(s["nation"]), "fleet": build_fleet(s["nation"])}
        if self.P["p2"]["ai"]:
            place_fleet_randomly(self.P["p2"]["board"], self.P["p2"]["fleet"])
        self.show_placement("p1")

    # ---------------- Uebergabebildschirm (Hotseat) ----------------
    def show_pass(self, to_name, hint, callback, button_text=None):
        """Verdeckt den Bildschirm, damit der andere Spieler nichts sieht."""
        self.screen = "pass"
        self.sound.play("uebergabe")
        self.clear()
        c = self.canvas
        draw_planks(c)
        draw_parchment(c, 250, 130, 850, 570)
        c.create_text(550, 200, text="Pass the computer to", font=(FONT, 22, "italic"), fill=INK)
        c.create_text(550, 270, text="Captain " + to_name, font=(FONT, 34, "bold"), fill="#8b1a1a")
        c.create_text(550, 345, text=hint, font=(FONT, 14, "italic"), fill=INK, width=480, justify="center")
        self.button(550, 450, 400, 62, button_text or ("I am Captain " + short(to_name, 16)),
                    callback, "btn_pass", size=20)

    # ---------------- Schiffe platzieren ----------------
    def cur_board(self):
        return self.P[self.placing]["board"]

    def cur_fleet(self):
        return self.P[self.placing]["fleet"]

    def show_placement(self, who):
        self.session += 1
        self.screen = "placement"
        self.placing = who
        self.clear()
        self.sel = 0
        self.horizontal = True
        self.hover = None
        self.redraw_placement()

    def placed_ids(self):
        return {s["id"] for s in self.cur_board()["ships"]}

    def next_unplaced(self):
        placed = self.placed_ids()
        for i in range(len(self.cur_fleet())):
            if i not in placed:
                return i
        return None

    def redraw_placement(self):
        c = self.canvas
        c.delete("all")
        draw_planks(c)
        me = self.P[self.placing]
        fleet, board = self.cur_fleet(), self.cur_board()
        self.shadow_text(550, 48, "Deploy your fleet, Captain %s" % me["name"], 26)
        self.button(104, 38, 190, 36, "Captain's Quarters", self.placement_back, "btn_back", size=11)
        self.sound_button(1010, 38)
        c.create_text(550, 92, text="Left click: place ship   |   Right click or R: rotate   |   "
                                    "Click a placed ship to move it",
                      font=(FONT, 13, "italic"), fill="#f6e7c1")
        x0, y0 = PLACE_POS
        draw_board(c, board, x0, y0, PLACE_CELL, show_ships=True, nation=me["nation"])
        draw_parchment(c, 580, 115, 1040, 655)
        c.create_text(810, 138, text="Your fleet (%s)" % me["nation"], font=(FONT, 16, "bold italic"), fill=INK)
        placed = self.placed_ids()
        for i, entry in enumerate(fleet):
            y = 170 + i * 29
            tag = "row%d" % i
            is_sel = i == self.sel
            c.create_rectangle(595, y - 13, 1025, y + 13, fill="#f7e6b0" if is_sel else PARCHMENT,
                               outline="#b8860b" if is_sel else "#c8b27a", width=2 if is_sel else 1,
                               tags=(tag,))
            c.create_text(610, y, anchor="w", text=entry["name"], font=(FONT, 13, "bold" if is_sel else "normal"),
                          fill=INK, tags=(tag,))
            for k in range(entry["size"]):
                c.create_rectangle(800 + k * 20, y - 7, 816 + k * 20, y + 7,
                                   fill="#3b2a1a" if i in placed else "#b89a5a", outline="#1a0f08", tags=(tag,))
            c.create_text(1015, y, anchor="e", text="placed" if i in placed else "-",
                          font=(FONT, 11, "italic"), fill="#2e5d1a" if i in placed else "#7a5a2a", tags=(tag,))
            self.bind_click(tag, lambda i=i: self.select_row(i))
        self.button(660, 548, 130, 42, "Rotate", self.rotate, "btn_rot", size=14)
        self.button(810, 548, 130, 42, "Random", self.random_fleet, "btn_rnd", size=14)
        self.button(960, 548, 130, 42, "Reset", self.reset_fleet, "btn_reset", size=14)
        ready = len(board["ships"]) == len(fleet)
        last = self.mode == "ai" or self.placing == "p2"
        self.button(810, 612, 270, 56, "Open Fire!" if last else "Ready", self.placement_done,
                    "btn_fire", size=22, enabled=ready)
        self.draw_placement_preview()

    def draw_placement_preview(self):
        c = self.canvas
        c.delete("preview")
        if self.hover is None or self.sel is None:
            return
        entry = self.cur_fleet()[self.sel]
        cells = ship_cells(self.hover[0], self.hover[1], entry["size"], self.horizontal)
        valid = can_place(self.cur_board(), cells)
        x0, y0 = PLACE_POS
        for (r, col) in cells:
            if in_grid(r, col):
                c.create_rectangle(x0 + col * PLACE_CELL + 2, y0 + r * PLACE_CELL + 2,
                                   x0 + (col + 1) * PLACE_CELL - 2, y0 + (r + 1) * PLACE_CELL - 2,
                                   fill="#58a55c" if valid else "#c0392b", outline="#1d3a1f",
                                   width=2, tags=("preview",))

    def select_row(self, i):
        self.sound.play("klick")
        board = self.cur_board()
        for ship in list(board["ships"]):
            if ship["id"] == i:
                board["ships"].remove(ship)
        self.sel = i
        self.redraw_placement()

    def placement_back(self):
        """Zurueck zu den Captain's Quarters; Eingaben bleiben erhalten, platzierte Schiffe verfallen."""
        if self.mode == "pvp" and self.placing == "p2":
            self.show_setup(2, keep=True)
        else:
            self.show_setup(1, keep=True)

    def rotate(self):
        self.sound.play("schiff_drehen")
        self.horizontal = not self.horizontal
        self.draw_placement_preview()

    def random_fleet(self):
        self.sound.play("random")
        place_fleet_randomly(self.cur_board(), self.cur_fleet())
        self.sel = None
        self.redraw_placement()

    def reset_fleet(self):
        self.sound.play("reset")
        self.cur_board()["ships"] = []
        self.sel = 0
        self.redraw_placement()

    def on_rotate_key(self, event):
        if self.screen == "placement":
            self.rotate()

    def placement_click(self, cell):
        board = self.cur_board()
        if self.sel is not None:
            entry = self.cur_fleet()[self.sel]
            cells = ship_cells(cell[0], cell[1], entry["size"], self.horizontal)
            if can_place(board, cells):
                add_ship(board, entry, cells, self.sel)
                self.sound.play("schiff_setzen")
                self.sel = self.next_unplaced()
                self.redraw_placement()
                return
        ship = ship_at(board, cell)
        if ship is not None:
            board["ships"].remove(ship)
            self.sound.play("klick")
            self.sel = ship["id"]
            self.horizontal = len({r for r, _ in ship["cells"]}) == 1
            self.redraw_placement()
            return
        if self.sel is not None:
            self.sound.play("ungueltig")

    def placement_done(self):
        self.sound.play("klick" if (self.mode == "pvp" and self.placing == "p1") else "open_fire")
        if self.mode == "pvp" and self.placing == "p1":
            second = self.P["p2"]["name"]
            self.show_pass(second, "Captain %s: your fleet is hidden now.\nHand the computer over!"
                           % self.P["p1"]["name"], lambda: self.show_placement("p2"))
        else:
            self.start_battle()

    # ---------------- Kampf: Start ----------------
    def start_battle(self):
        self.session += 1
        self.screen = "battle"
        for who in ("p1", "p2"):
            self.P[who]["points"] = 0
        self.log = []
        self.overlay = None
        self.banner_msg = None
        self.reveal = False
        self.hover = None
        self.shots_left = 1
        self.special = {"p1": None, "p2": None}
        self.skip = {"p1": False, "p2": False}
        self.inventory = {"p1": [], "p2": []}
        self.turn_no = 0
        self.viewer = "p1" if self.mode == "ai" else None
        self.say("The %s fleet appears on the horizon!" % self.P["p2"]["nation"])
        self.phase = "busy"
        self.coin_toss(random.choice(["p1", "p2"]))

    # ---------------- Muenzwurf vor Kampfbeginn ----------------
    COIN_MS = 40
    COIN_T = 2.2
    COIN_HOLD_MS = 1700

    def coin_toss(self, first):
        """Kopf = Spieler 1 beginnt, Zahl = Spieler 2 (bzw. der Gegner)."""
        if self.mode == "ai":
            who = self.P["p1"]["name"]
            text = ("Heads! You fire first, Captain %s!" % who if first == "p1"
                    else "Tails! The enemy fires first!")
            logtext = ("The coin toss decides: you fire first, Captain %s!" % who if first == "p1"
                       else "The coin toss decides: the enemy fires first!")
        else:
            name = self.P[first]["name"]
            text = "%s! Captain %s fires first!" % ("Heads" if first == "p1" else "Tails", name)
            logtext = "The coin toss decides: Captain %s fires first!" % name
        self.say(logtext)
        self.coin_first = first
        self.coin_text = text
        self.canvas.delete("all")
        draw_battle_background(self.canvas)
        self.shadow_text(550, 38, "BATTLE OF TRAFALGAR", 28)
        self.shadow_text(550, 72, "The %s fleet appears on the horizon!" % self.P["p2"]["nation"],
                         14, "#f6e7c1", "italic")
        self.sound_button(1010, 38)
        self.canvas.create_rectangle(0, 528, WIDTH, HEIGHT, fill="#563822", outline="")
        for x in range(0, WIDTH, 110):
            self.canvas.create_line(x, 528, x - 30, HEIGHT, fill="#34200f", width=2)
        self.canvas.create_line(0, 528, WIDTH, 528, fill="#28160b", width=4)
        self.sound.play("muenzwurf", "coin")
        self.coin_frame(0)

    def coin_frame(self, i):
        c = self.canvas
        c.delete("coin")
        t = i * self.COIN_MS / 1000.0
        cx, ground, R = 550, 500, 66
        t_up, t_land = 0.15, 1.20
        turns = 8 * math.pi if self.coin_first == "p1" else 9 * math.pi   # gerade = Kopf (Anker)
        if t < t_up:
            lift, ang = 0.0, 0.0
        elif t < t_land:
            u = (t - t_up) / (t_land - t_up)
            lift = 4 * u * (1 - u) * 270
            ang = turns * (u ** 0.9)
        else:
            sec = t - t_land
            lift = max(0.0, 30 * math.exp(-sec * 6) * abs(math.sin(sec * 14)))
            ang = turns + 0.25 * math.exp(-sec * 5) * math.sin(sec * 16)
        y = ground - lift
        sx = abs(math.cos(ang)) * R
        front = (math.cos(ang) >= 0)
        sh = max(16, R * 0.9 - lift * 0.1)
        c.create_oval(cx - sh, ground + R * 0.55 - 8, cx + sh, ground + R * 0.55 + 10,
                      fill="#2a1a0e", outline="", tags=("coin",))
        rim = "#b08016" if front else "#966a10"
        face = "#f0c43c" if front else "#deb02c"
        c.create_oval(cx - max(sx, 4), y - R, cx + max(sx, 4), y + R, fill=rim, outline="#5a3c08",
                      width=3, tags=("coin",))
        ink = "#6e4c0a"
        if sx > 11:
            c.create_oval(cx - sx + 10, y - R + 10, cx + sx - 10, y + R - 10, fill=face,
                          outline="#be8c14", width=2, tags=("coin",))
            k = sx / R
            if front:      # Vorderseite: Anker
                c.create_line(cx, y - 34, cx, y + 31, fill=ink, width=max(1, int(7 * k)), tags=("coin",))
                c.create_line(cx - 20 * k, y - 17, cx + 20 * k, y - 17, fill=ink,
                              width=max(1, int(5 * k)), tags=("coin",))
                c.create_arc(cx - 29 * k, y + 3, cx + 29 * k, y + 43, start=180, extent=180, style="arc",
                             outline=ink, width=max(1, int(5 * k)), tags=("coin",))
            else:          # Rueckseite: Kreuz
                c.create_line(cx, y - 31, cx, y + 31, fill=ink, width=max(1, int(8 * k)), tags=("coin",))
                c.create_line(cx - 26 * k, y, cx + 26 * k, y, fill=ink, width=max(1, int(8 * k)), tags=("coin",))
        if t > t_land + 0.35:
            c.create_text(550, 190, text=self.coin_text, font=(FONT, 27, "bold"), fill="#120a05", tags=("coin",))
            c.create_text(547, 187, text=self.coin_text, font=(FONT, 27, "bold"), fill="#f6e7c1", tags=("coin",))
        elif t < t_up + 0.6:
            c.create_text(550, 190, text="The coin toss decides...", font=(FONT, 20, "italic"),
                          fill="#f6e7c1", tags=("coin",))
        if t < self.COIN_T:
            self.later(self.COIN_MS, lambda: self.coin_frame(i + 1))
        else:
            self.later(self.COIN_HOLD_MS, lambda: self.start_turn(self.coin_first))

    # ---------------- Kampf: Zugablauf ----------------
    def start_turn(self, who):
        if self.skip[who]:
            self.skip[who] = False
            lose = "lose" if self.actor(who) == "You" else "loses"
            self.say("%s %s a turn: the fireship threw the fleet into chaos!" % (self.actor(who), lose))
            self.turn = opp(who)
            self.turn_no += 1
            self.shots_left = 1
            self.redraw_battle()
            self.later(1500, self.continue_turn)
            return
        self.turn = who
        self.turn_no += 1
        self.shots_left = 1
        if self.mode == "pvp" and who != self.viewer:
            self.phase = "busy"
            if self.viewer is None:
                self.show_handover()
            else:
                self.later(1800, self.show_handover)     # Zeit, das Ergebnis des Schusses zu sehen
        else:
            self.continue_turn()

    def show_handover(self):
        name = self.P[self.turn]["name"]
        self.show_pass(name, "The other captain must look away now.\nYour fleet is hidden until you click.",
                       self.end_handover)

    def end_handover(self):
        self.screen = "battle"
        self.viewer = self.turn
        self.continue_turn()

    def continue_turn(self):
        me = self.P[self.turn]
        if me["ai"]:
            self.ai_use_prizes(self.turn)
            self.phase = "ai_turn"
            self.say("The enemy takes aim...")
            self.sound.play("computer_denkt")
            self.redraw_battle()
            self.later(1100, self.ai_move)
        else:
            self.phase = "human_turn"
            if self.mode == "ai":
                self.say("Your turn, Captain %s! Right-click a square to fire." % me["name"])
            else:
                self.say("Captain %s, it is your turn! Right-click a square to fire." % me["name"])
            self.redraw_battle()

    def after_shot(self):
        if self.shots_left > 0:
            self.continue_turn()
        else:
            self.start_turn(opp(self.turn))

    def ai_move(self):
        if self.phase != "ai_turn":
            return
        self.process_shot("p2", ai_choose_shot(self.P["p1"]["board"], self.difficulty))

    def process_shot(self, who, cell):
        """Schuss abfeuern: erst Kanonendonner, nach der Flugzeit kommt das Ergebnis."""
        tw = opp(who)
        target = self.P[tw]["board"]
        kind = self.special[who]
        if kind:
            cells = [x for x in pattern_cells(kind, cell) if x not in target["shots"]]
            if not cells:
                return
            self.special[who] = None
        else:
            cells = [cell]
        self.shots_left -= 1
        self.phase = "busy"
        self.sound.play("kanonenschuss")
        self.redraw_battle()
        self.later(SHOT_FLIGHT_MS, lambda: self.resolve_shot(who, cell, kind, cells))

    def resolve_shot(self, who, cell, kind, cells):
        tw = opp(who)
        target = self.P[tw]["board"]
        results = [fire(target, x) for x in cells]
        self.P[who]["points"] += sum(1 for r in results if r["result"] != "miss")
        self.report_shot(who, tw, cell, kind, results)
        self.phase = "busy"
        self.redraw_battle()
        origin = BATTLE_OWN_POS if tw == self.viewer else BATTLE_ENEMY_POS
        any_hit = any(r["result"] != "miss" for r in results)
        any_gold = any(r["result"] == "treasure" for r in results)
        any_sunk = any(r["sunk"] and r["ship"]["kind"] != "treasure" for r in results)
        self.sound.play("schatzschiff" if any_gold else "versenkt" if any_sunk else "treffer" if any_hit else "fehlschuss")
        color = "#ffd84a" if any_gold else ("#ff7b3a" if any_hit else "#bfe0ff")
        self.explode(origin[0] + (cells[0][1] + 0.5) * BATTLE_CELL,
                     origin[1] + (cells[0][0] + 0.5) * BATTLE_CELL, color)
        if fleet_defeated(target):
            self.end_game(who)
            return
        if any_gold:
            self.open_chest(who)
            return
        self.after_shot()

    def report_shot(self, who, tw, cell, kind, results):
        actor, owner = self.actor(who), self.owner(tw)
        owner_cap = owner[0].upper() + owner[1:]
        sunk_now = [r["ship"] for r in results if r["sunk"] and r["ship"]["kind"] != "treasure"]
        if kind is None:
            res, name = results[0], cell_name(cell)
            if res["result"] == "miss":
                self.say("%s fired at %s: a miss, only water." % (actor, name))
            elif res["result"] == "treasure":
                self.say("%s fired at %s: the TREASURE SHIP is hit!" % (actor, name))
            elif res["sunk"]:
                self.say("%s fired at %s: %s %s is sunk!" % (actor, name, owner, res["ship"]["name"]))
            else:
                self.say("%s fired at %s: a hit!" % (actor, name))
        else:
            hits = sum(1 for r in results if r["result"] != "miss")
            title = PRIZE_INFO[kind][0].rstrip("!")
            self.say("%s fired a %s: %d hit(s), %d miss(es)." % (actor, title, hits, len(results) - hits))
            if any(r["result"] == "treasure" for r in results):
                self.say("%s hit the TREASURE SHIP!" % actor)
            for ship in sunk_now:
                self.say("%s %s is sunk!" % (owner_cap, ship["name"]))
        if sunk_now:
            self.banner_msg = ("SUNK!", sunk_now[-1]["name"], tw)
            self.later(2200, self.clear_banner)

    def retreat(self):
        self.sound.stop_all()
        self.sound.play("retreat")
        self.show_start()

    def toggle_sound(self):
        self.sound.enabled = not self.sound.enabled
        self.data["sound"] = self.sound.enabled
        save_data(self.data)
        if not self.sound.enabled:
            self.sound.stop_all()
        if self.screen == "battle":
            self.redraw_battle()
            return
        self.canvas.delete("btn_sound")
        self.sound_button(*self.snd_pos)
        if self.sound.enabled and self.screen == "start":
            self.start_bg()

    def clear_banner(self):
        self.banner_msg = None
        if self.screen == "battle":
            self.redraw_battle()

    def explode(self, x, y, color, step=0):
        c = self.canvas
        c.delete("fx")
        if step >= 5 or self.screen != "battle":
            return
        r = 6 + step * 7
        c.create_oval(x - r, y - r, x + r, y + r, outline=color, width=max(1, 5 - step), tags=("fx",))
        self.later(55, lambda: self.explode(x, y, color, step + 1))

    # ---------------- Truhe ----------------
    def open_chest(self, who):
        self.phase = "chest"
        self.sound.play("truhe")
        prize = random.choice(NATION_PRIZES[self.P[who]["nation"]])
        self.overlay = {"type": "chest", "who": who, "prize": prize, "stage": 0}
        self.redraw_battle()
        self.later(1200, self.chest_open_stage)

    def chest_open_stage(self):
        if not self.overlay or self.overlay["type"] != "chest":
            return
        self.overlay["stage"] = 1
        self.redraw_battle()
        if self.P[self.overlay["who"]]["ai"]:
            self.later(2600, self.finish_chest)

    def finish_chest(self):
        """Der Preis wird nicht sofort benutzt, sondern in den Laderaum gelegt."""
        if not self.overlay or self.overlay["type"] != "chest":
            return
        who, prize = self.overlay["who"], self.overlay["prize"]
        self.overlay = None
        self.store_prize(who, prize)
        self.redraw_battle()
        self.after_shot()

    def store_prize(self, who, prize):
        hold = self.inventory[who]
        if len(hold) >= MAX_CARGO:
            self.say("%s: the cargo hold is full, the prize is lost." % self.actor(who))
            return
        hold.append({"id": prize, "turn": self.turn_no})
        if self.mode == "ai" and who == "p1":
            self.say("%s stored in your cargo hold. Use it from your next turn!"
                     % PRIZE_INFO[prize][0].rstrip("!"))
        else:
            self.say("%s stored a prize in the cargo hold." % self.actor(who))

    def use_inventory(self, index):
        """Der Spieler waehlt einen gelagerten Preis (fruehestens in der naechsten Runde)."""
        if self.phase != "human_turn":
            return
        who = self.viewer
        hold = self.inventory[who]
        if index >= len(hold):
            return
        item = hold[index]
        if item["turn"] >= self.turn_no:
            self.say("This prize can be used from your next turn.")
            self.redraw_battle()
            return
        if item["id"] in ("broadside", "mortar") and self.special[who]:
            self.say("A special shot is already loaded.")
            self.redraw_battle()
            return
        hold.pop(index)
        self.use_prize(who, item["id"])

    def ai_use_prizes(self, who):
        """Der Computer setzt zu Beginn seines Zugs alle einsatzbereiten Preise ein."""
        for item in list(self.inventory[who]):
            prize = item["id"]
            if item["turn"] >= self.turn_no:
                continue
            if prize in ("broadside", "mortar") and self.special[who]:
                continue
            if prize == "repair" and "hit" not in self.P[who]["board"]["shots"].values():
                continue
            self.inventory[who].remove(item)
            self.use_prize(who, prize)

    def use_prize(self, who, prize):
        """Wirkung eines Preises. Der Zug geht danach normal weiter."""
        tw = opp(who)
        me, target, own = self.P[who], self.P[tw]["board"], self.P[who]["board"]
        actor = self.actor(who)
        if prize == "gunners":
            self.shots_left += 1
            self.say("%s gained an extra shot!" % actor)
        elif prize in ("broadside", "mortar"):
            self.special[who] = prize
            what = "3 squares in a row" if prize == "broadside" else "a 2x2 block"
            self.say("%s loaded a %s: the next shot hits %s!" % (actor, PRIZE_INFO[prize][0].rstrip("!"), what))
        elif prize == "signals":
            scout_cells(target, 4)
            if me["ai"]:
                self.say("The enemy's signal flags scout 4 squares of your waters!")
            else:
                self.say("%s: 4 squares revealed (diamond = ship, dot = water)." % actor)
        elif prize == "map":
            ship = reveal_ship(target)
            if ship is None:
                self.say("%s used a treasure map, but it shows nothing new." % actor)
            elif me["ai"]:
                self.say("The enemy used a treasure map of your fleet!")
            else:
                self.say("The map marks a whole enemy ship: a %s!" % ship["name"])
        elif prize == "fireship":
            self.skip[tw] = True
            lose = "lose" if self.actor(tw) == "You" else "loses"
            self.say("A fireship drifts into the line: %s %s the next turn!" % (self.actor(tw), lose))
        elif prize == "gold":
            me["points"] += 5
            self.say("%s won 5 points in gold doubloons!" % actor)
        elif prize == "repair":
            cell = repair_one(own)
            if cell is None:
                self.say("%s has nothing to repair yet." % actor)
            else:
                self.say("%s repaired the damage at %s." % (actor, cell_name(cell)))
        else:   # reinforcement: neues Ein-Kaestchen-Schiff
            if me["ai"]:
                place_randomly(own, {"name": "Prize Ship", "kind": "prize", "size": 1})
                self.say("The enemy gained a Prize Ship!")
            else:
                self.phase = "place_prize"
                self.say("Reinforcement! Left-click an empty square on YOUR fleet to place the ship.")
                self.redraw_battle()
                return
        self.redraw_battle()

    def prize_ship_placed(self, cell):
        own = self.P[self.viewer]["board"]
        if ship_at(own, cell) is not None or cell in own["shots"]:
            self.say("Choose an empty square the enemy has not fired at yet.")
            self.redraw_battle()
            return
        add_ship(own, {"name": "Prize Ship", "kind": "prize", "size": 1}, [cell])
        self.say("Your Prize Ship is ready at %s. Your turn goes on!" % cell_name(cell))
        self.hover = None
        self.phase = "human_turn"
        self.redraw_battle()

    # ---------------- Spielende ----------------
    def end_game(self, winner):
        self.phase = "gameover"
        self.reveal = True
        totals = {}
        if self.mode == "ai":
            totals["p1"] = record_result(self.data, self.P["p1"]["name"], self.P["p1"]["points"],
                                         winner == "p1", self.difficulty)
        else:
            for who in ("p1", "p2"):
                totals[who] = record_result(self.data, self.P[who]["name"], self.P[who]["points"],
                                            who == winner, "Hotseat")
        self.overlay = {"type": "gameover", "winner": winner, "totals": totals}
        self.sound.play("niederlage" if (self.mode == "ai" and winner != "p1") else "sieg")
        self.redraw_battle()

    # ---------------- Kampfbildschirm zeichnen ----------------
    def redraw_battle(self):
        c = self.canvas
        c.delete("all")
        draw_battle_background(c)
        self.shadow_text(550, 38, "BATTLE OF TRAFALGAR", 28)
        self.shadow_text(550, 72, "Cape Trafalgar, 21 October 1805", 12, "#f6e7c1", "italic")
        self.button(1010, 38, 130, 36, "Retreat", self.retreat, "btn_retreat", size=12)
        self.sound_button(892, 38)

        v = self.viewer
        mine, other = self.P[v], self.P[opp(v)]
        ex, ey = BATTLE_ENEMY_POS
        ox, oy = BATTLE_OWN_POS
        draw_flag(c, other["nation"], ex, 88, 40, 26)
        c.create_text(ex + 52, 94, anchor="w", text=other["name"], font=(FONT, 13, "bold"), fill="#f6e7c1")
        c.create_text(ex + 52, 112, anchor="w", text="Enemy waters (%s): right mouse button = fire"
                      % other["nation"], font=(FONT, 10, "italic"), fill=GOLD)
        draw_flag(c, mine["nation"], ox, 88, 40, 26)
        c.create_text(ox + 52, 94, anchor="w", text=mine["name"], font=(FONT, 13, "bold"), fill="#f6e7c1")
        if self.phase == "place_prize":
            c.create_text(ox + 52, 112, anchor="w", text="Click an empty square to place your ship!",
                          font=(FONT, 11, "bold italic"), fill="#ffd24d")
        else:
            c.create_text(ox + 52, 112, anchor="w", text="Your fleet (%s)" % mine["nation"],
                          font=(FONT, 11, "italic"), fill=GOLD)
        draw_board(c, other["board"], ex, ey, BATTLE_CELL, show_ships=self.reveal,
                   nation=other["nation"], show_scouted=True)
        draw_board(c, mine["board"], ox, oy, BATTLE_CELL, show_ships=True, nation=mine["nation"])
        if self.phase == "place_prize":
            size = GRID * BATTLE_CELL
            c.create_rectangle(ox - 12, oy - 12, ox + size + 12, oy + size + 12,
                               outline="#ffd24d", width=4)
        if self.banner_msg:
            text, ship_name, board_owner = self.banner_msg
            bx, by = BATTLE_OWN_POS if board_owner == v else BATTLE_ENEMY_POS
            self.shadow_text(bx + 190, by + 170, text, 44, "#ff5a47")
            self.shadow_text(bx + 190, by + 218, ship_name, 20, "#f6e7c1")
        self.draw_center_panel()
        self.draw_cargo()
        self.draw_log()
        self.draw_overlay()

    def draw_center_panel(self):
        c = self.canvas
        v = self.viewer
        mine, other = self.P[v], self.P[opp(v)]
        draw_parchment(c, 465, 140, 635, 535)
        cx = 550
        if self.phase == "gameover":
            turn_text, turn_color = "Battle over", INK
        elif self.phase == "chest":
            turn_text, turn_color = "Treasure!", "#8a6d1f"
        elif self.P[self.turn]["ai"]:
            turn_text, turn_color = "Enemy turn", "#8b1a1a"
        elif self.mode == "ai":
            turn_text, turn_color = "Your turn", "#1d6b2b"
        else:
            turn_text, turn_color = "%s's turn" % short(self.P[self.turn]["name"]), "#1d6b2b"
        c.create_text(cx, 166, text=turn_text, font=(FONT, 16, "bold italic"), fill=turn_color)
        extra = []
        kind = self.special.get(v) if self.phase == "human_turn" else None
        if kind:
            extra.append("%s armed" % PRIZE_SHORT[kind][0])
        if self.phase == "human_turn" and self.shots_left > 1:
            extra.append("%d shots left" % self.shots_left)
        for i, text in enumerate(extra):
            c.create_text(cx, 188 + i * 16, text=text, font=(FONT, 11, "italic"), fill=INK)
        n1 = "You" if self.mode == "ai" else short(mine["name"])
        n2 = "Enemy" if self.mode == "ai" else short(other["name"])
        c.create_line(485, 218, 615, 218, fill="#b89a5a")
        c.create_text(cx, 236, text="Points", font=(FONT, 14, "bold"), fill=INK)
        c.create_text(cx, 262, text="%s: %d" % (n1, mine["points"]), font=(FONT, 15, "bold"), fill="#1d3a6b")
        c.create_text(cx, 288, text="%s: %d" % (n2, other["points"]), font=(FONT, 15, "bold"), fill="#8b1a1a")
        c.create_line(485, 312, 615, 312, fill="#b89a5a")
        c.create_text(cx, 328, text="Fleets", font=(FONT, 14, "bold"), fill=INK)
        c.create_text(578, 347, anchor="e", text="afloat", font=(FONT, 10, "italic"), fill="#6b5233")
        c.create_text(614, 347, anchor="e", text="sunk", font=(FONT, 10, "italic"), fill="#6b5233")
        for i, (nm, side) in enumerate(((n1, mine), (n2, other))):
            board = side["board"]
            afloat = ships_afloat(board)
            sunk = sum(1 for sh in board["ships"] if sh["kind"] != "treasure" and is_sunk(sh))
            y = 368 + i * 22
            c.create_text(488, y, anchor="w", text=nm, font=(FONT, 12), fill=INK)
            c.create_text(574, y, anchor="e", text=str(afloat), font=(FONT, 14, "bold"), fill=INK)
            c.create_text(614, y, anchor="e", text=str(sunk), font=(FONT, 14, "bold"), fill="#8b1a1a")
        c.create_line(485, 402, 615, 402, fill="#b89a5a")
        legend = [(HIT_RED, "Hit"), (MISS_BLUE, "Miss"), (TREASURE_GOLD, "Treasure")]
        for i, (color, label) in enumerate(legend):
            y = 424 + i * 22
            c.create_rectangle(490, y - 8, 506, y + 8, fill=color, outline="#1a0f08")
            c.create_text(520, y, anchor="w", text=label, font=(FONT, 12), fill=INK)
        y = 424 + 3 * 22
        c.create_polygon(498, y - 8, 507, y, 498, y + 8, 489, y, fill="#5a1010", outline="#1a0f08")
        c.create_text(520, y, anchor="w", text="Spotted", font=(FONT, 12), fill=INK)
        y = 424 + 4 * 22
        draw_skull(c, 498, y, 8)
        c.create_text(520, y, anchor="w", text="Ship sunk", font=(FONT, 12), fill=INK)

    def draw_cargo(self):
        """Laderaum: gelagerte Preise. Ein Klick setzt einen Preis ein (ab der naechsten Runde)."""
        c = self.canvas
        v = self.viewer
        hold = self.inventory[v]
        c.create_rectangle(70, 548, 1030, 592, fill="#3a2512", outline=GOLD, width=2)
        c.create_text(84, 570, anchor="w", text="Cargo hold", font=(FONT, 12, "bold italic"), fill=GOLD)
        x0, x1 = 192, 840
        if not hold:
            c.create_rectangle(x0, 553, x1, 587, outline="#6b5233", dash=(3, 3))
            c.create_text((x0 + x1) // 2, 570, text="empty - hit the Treasure Ship to win a prize",
                          font=(FONT, 11, "italic"), fill="#a58b5c")
        else:
            item = hold[0]
            usable = item["turn"] < self.turn_no
            name = PRIZE_INFO[item["id"]][0].rstrip("!")
            text = PRIZE_INFO[item["id"]][1] if usable else "usable from your next turn"
            c.create_rectangle(x0, 553, x1, 587, fill="#e8d7a8" if usable else "#8a7a55",
                               outline="#f2c94c" if usable else "#5a4a2a", width=2, tags=("chip0",))
            c.create_text(x0 + 12, 570, anchor="w", text=name, font=(FONT, 12, "bold"), fill=INK,
                          tags=("chip0",))
            c.create_text(x1 - 12, 570, anchor="e", text=text, font=(FONT, 11, "italic"),
                          fill="#6b4a22" if usable else "#f0e2b8", tags=("chip0",))
            self.bind_click("chip0", lambda: self.use_inventory(0))
        c.create_text(1018, 570, anchor="e", text="Enemy: %s" % ("1 prize" if self.inventory[opp(v)] else "none"),
                      font=(FONT, 11, "italic"), fill="#f6e7c1")

    def draw_log(self):
        c = self.canvas
        draw_parchment(c, 70, 598, 1030, 692)
        lines = self.log[-3:]
        for i, line in enumerate(lines):
            newest = i == len(lines) - 1
            c.create_text(92, 621 + i * 24, anchor="w", text=line,
                          font=(FONT, 14, "bold" if newest else "normal"),
                          fill=INK if newest else "#6b5233")

    def draw_overlay(self):
        ov = self.overlay
        if not ov:
            return
        c = self.canvas
        if ov["type"] == "chest":
            self.draw_chest_overlay(ov)
            return
        draw_parchment(c, 300, 150, 800, 550)
        winner = ov["winner"]
        p1, p2 = self.P["p1"], self.P["p2"]
        if self.mode == "ai":
            won = winner == "p1"
            c.create_text(550, 225, text="VICTORY" if won else "DEFEAT", font=(FONT, 60, "bold"),
                          fill="#1d6b2b" if won else "#8b1a1a")
            msg = ("The fleet of %s is destroyed, Captain %s!" % (p2["name"], p1["name"]) if won
                   else "Your fleet lies on the sea floor, Captain %s." % p1["name"])
            c.create_text(550, 288, text=msg, font=(FONT, 13, "italic"), fill=INK, width=460, justify="center")
            c.create_text(550, 342, text="Your points: %d" % p1["points"], font=(FONT, 26, "bold"), fill="#1d3a6b")
            c.create_text(550, 384, text="Enemy points: %d" % p2["points"], font=(FONT, 16), fill="#8b1a1a")
            c.create_text(550, 422, text="Total points of Captain %s: %d" % (p1["name"], ov["totals"]["p1"]),
                          font=(FONT, 14, "bold"), fill=INK)
        else:
            c.create_text(550, 225, text="VICTORY", font=(FONT, 60, "bold"), fill="#1d6b2b")
            c.create_text(550, 288, text="Captain %s wins the Battle of Trafalgar!" % self.P[winner]["name"],
                          font=(FONT, 14, "italic"), fill=INK, width=460, justify="center")
            for i, who in enumerate(("p1", "p2")):
                c.create_text(550, 338 + i * 40, font=(FONT, 17, "bold"),
                              fill="#1d3a6b" if i == 0 else "#8b1a1a",
                              text="%s: %d points (total %d)" % (self.end_name(who),
                                                                 self.P[who]["points"], ov["totals"][who]))
        self.button(550, 495, 260, 56, "Return to Port", self.show_start, "btn_port", size=20)

    def end_name(self, who):
        name = self.P[who]["name"]
        if self.P[who].get("ai"):
            if "Nelson" in name:
                return "Lord Nelson"
            if "Villeneuve" in name:
                return "Villeneuve"
            if "Gravina" in name:
                return "Gravina"
        return short(name, 16)

    def draw_chest_overlay(self, ov):
        c = self.canvas
        draw_parchment(c, 330, 170, 770, 540)
        who, stage = ov["who"], ov["stage"]
        c.create_text(550, 208, text="%s found the treasure!" % self.actor(who),
                      font=(FONT, 17 if self.P[who]["ai"] else 20, "bold italic"), fill=INK,
                      width=410, justify="center")
        bx0, by0, bx1, by1 = 500, 360, 600, 420
        c.create_rectangle(bx0, by0, bx1, by1, fill="#7a4a1e", outline="#2a1a10", width=3)
        c.create_rectangle(bx0 + 10, by0, bx0 + 22, by1, fill="#d9a441", outline="#2a1a10")
        c.create_rectangle(bx1 - 22, by0, bx1 - 10, by1, fill="#d9a441", outline="#2a1a10")
        if stage == 0:
            c.create_arc(bx0, by0 - 40, bx1, by0 + 40, start=0, extent=180, style="chord",
                         fill="#8a5624", outline="#2a1a10", width=3)
            c.create_rectangle(545, by0 + 8, 555, by0 + 28, fill="#f2c94c", outline="#2a1a10")
            c.create_text(550, 455, text="A chest rises from the waves...",
                          font=(FONT, 16, "italic"), fill=INK)
            return
        c.create_polygon(bx0, by0, bx1, by0, bx1 - 8, by0 - 52, bx0 + 8, by0 - 52,
                         fill="#5e3814", outline="#2a1a10", width=3)
        c.create_oval(bx0 + 8, by0 - 10, bx1 - 8, by0 + 14, fill="#ffe27a", outline="#d9a441", width=2)
        prize = ov["prize"]
        if self.P[who]["ai"]:
            # Der Preis des Computers bleibt geheim
            c.create_text(550, 262, text="?", font=(FONT, 60, "bold"), fill="#8a6d1f")
            c.create_text(550, 440, text="The enemy takes a prize", font=(FONT, 18, "bold"), fill="#8a6d1f")
            c.create_text(550, 464, text="You do not know what it is...", font=(FONT, 12, "italic"), fill=INK)
            return
        draw_prize_icon(c, prize, 550, 262)
        title, sub = PRIZE_INFO[prize]
        c.create_text(550, 440, text=title, font=(FONT, 18, "bold"), fill="#8a6d1f")
        c.create_text(550, 464, text=sub, font=(FONT, 12, "italic"), fill=INK)
        c.create_text(550, 484, text="It goes into the cargo hold: usable from the next turn.",
                      font=(FONT, 11, "italic"), fill="#6b5233")
        if not self.P[who]["ai"]:
            self.button(550, 516, 220, 36, "Take the prize", self.finish_chest, "btn_prize", size=14)

    # ---------------- Mausbedienung ----------------
    def on_left(self, e):
        if e.time == self._btn_time:
            return
        if self.screen == "placement":
            cell = cell_at(e.x, e.y, PLACE_POS[0], PLACE_POS[1], PLACE_CELL)
            if cell is not None:
                self.placement_click(cell)
        elif self.screen == "battle" and self.phase == "place_prize":
            cell = cell_at(e.x, e.y, BATTLE_OWN_POS[0], BATTLE_OWN_POS[1], BATTLE_CELL)
            if cell is not None:
                self.prize_ship_placed(cell)

    def on_right(self, e):
        if e.time == self._btn_time:
            return
        if self.screen == "placement":
            self.rotate()
        elif self.screen == "battle" and self.phase == "human_turn":
            cell = cell_at(e.x, e.y, BATTLE_ENEMY_POS[0], BATTLE_ENEMY_POS[1], BATTLE_CELL)
            if cell is None:
                return
            enemy = self.P[opp(self.viewer)]["board"]
            kind = self.special[self.viewer]
            if all(x in enemy["shots"] for x in pattern_cells(kind, cell)):
                self.say("You already fired there, Captain!")
                self.redraw_battle()
                return
            if kind is None and cell in enemy["shots"]:
                return
            self.process_shot(self.viewer, cell)

    def on_motion(self, e):
        if self.screen == "placement":
            cell = cell_at(e.x, e.y, PLACE_POS[0], PLACE_POS[1], PLACE_CELL)
            if cell != self.hover:
                self.hover = cell
                self.draw_placement_preview()
        elif self.screen == "battle" and self.phase == "place_prize":
            cell = cell_at(e.x, e.y, BATTLE_OWN_POS[0], BATTLE_OWN_POS[1], BATTLE_CELL)
            if cell != self.hover:
                self.hover = cell
                self.canvas.delete("preview")
                if cell is not None:
                    own = self.P[self.viewer]["board"]
                    free = ship_at(own, cell) is None and cell not in own["shots"]
                    ox, oy = BATTLE_OWN_POS
                    self.canvas.create_rectangle(
                        ox + cell[1] * BATTLE_CELL + 2, oy + cell[0] * BATTLE_CELL + 2,
                        ox + (cell[1] + 1) * BATTLE_CELL - 2, oy + (cell[0] + 1) * BATTLE_CELL - 2,
                        fill="#58a55c" if free else "#c0392b", outline="#1d3a1f", width=2, tags=("preview",))
        elif (self.screen == "battle" and self.phase == "human_turn"
              and self.special.get(self.viewer)):
            cell = cell_at(e.x, e.y, BATTLE_ENEMY_POS[0], BATTLE_ENEMY_POS[1], BATTLE_CELL)
            if cell != self.hover:
                self.hover = cell
                self.canvas.delete("preview")
                if cell is not None:
                    ex, ey = BATTLE_ENEMY_POS
                    for (r, col) in pattern_cells(self.special[self.viewer], cell):
                        self.canvas.create_rectangle(
                            ex + col * BATTLE_CELL + 2, ey + r * BATTLE_CELL + 2,
                            ex + (col + 1) * BATTLE_CELL - 2, ey + (r + 1) * BATTLE_CELL - 2,
                            outline="#ff9d2e", width=3, tags=("preview",))


def main():
    root = tk.Tk()
    TrafalgarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
