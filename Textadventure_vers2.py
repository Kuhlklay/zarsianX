import time
import random
# import asyncio
import json
import string


# -----------------------------
# Klasse Inventar
# Das Inventar hat 3 Slots, wobei in jedem Slot maximal 5 gleiche Items gestapelt werden können.
# Somit sind insgesamt maximal 15 Items möglich.
# -----------------------------
class Inventar:
    def __init__(self):
        # Jeder Slot ist ein Dictionary mit "item" und "count"
        self.slots = []
        self.max_slots = 5
        self.max_per_slot = 20

    def add_item(self, item, quantity=1):
        # Versuche, vorhandene Stapel zum Auffüllen zu verwenden
        for slot in self.slots:
            if slot["item"] == item and slot["count"] < self.max_per_slot:
                space = self.max_per_slot - slot["count"]
                add_here = min(space, quantity)
                slot["count"] += add_here
                quantity -= add_here
                if quantity == 0:
                    return True
        # Falls noch Menge übrig ist, füge neue Slots hinzu – sofern noch Platz im Inventar vorhanden ist
        while quantity > 0:
            if len(self.slots) < self.max_slots:
                add_here = min(self.max_per_slot, quantity)
                self.slots.append({"item": item, "count": add_here})
                quantity -= add_here
            else:
                print(f"Kein freier Platz im Inventar für {item}!")
                return False
        return True

    def remove_item(self, item, quantity=1):
        removed = 0
        for slot in self.slots:
            if slot["item"] == item:
                can_remove = min(slot["count"], quantity - removed)
                slot["count"] -= can_remove
                removed += can_remove
        # Leere Slots entfernen
        self.slots = [slot for slot in self.slots if slot["count"] > 0]
        if removed < quantity:
            print(f"Nicht genügend {item} zum Entfernen.")
            return False
        return True

    def total_items_of(self, item):
        total = 0
        for slot in self.slots:
            if slot["item"] == item:
                total += slot["count"]
        return total

    def total_items(self):
        return sum(slot["count"] for slot in self.slots)

    def has_item(self, item, quantity=1):
        return self.total_items_of(item) >= quantity

    def __str__(self):
        if not self.slots:
            return "Inventar ist leer."
        output = "\n╔════════════════╦═══════╗\n"
        output += "║   Item         ║ Menge ║\n"
        output += "╠════════════════╬═══════╣\n"
        for slot in self.slots:
            output += f"║ {slot['item']:<14} ║ {slot['count']:>5} ║\n"
        output += "╚════════════════╩═══════╝"
        output += f"\nGesamt: {self.total_items()} Items"
        output+= f"\nRwo: {Spieler.money}",
        return output

# -----------------------------
# Klasse Spitzhacke
# Die Spitzhacke besitzt fünf Aufwertungsstufen: Holz, Stein, Eisen, Gold und Diamant.
# Für den Start ist der Spieler mit der Holzspitzhacke ausgestattet.
# Außerdem beeinflusst der Typ der Spitzhacke die Abbauzeit.
# -----------------------------
class Spitzhacke:
    def __init__(self):
        self.level_names = ["Holz", "Stein", "Eisen", "Gold", "Diamant"]
        self.level = 0  # Start: Holz
        self.set_mining_time()

    def upgrade(self):
        if self.level < len(self.level_names) - 1:
            self.level += 1
            self.set_mining_time()
            print(f"Spitzhacke aufgewertet zu {self.level_names[self.level]}!")
        else:
            print("Maximale Aufwertung erreicht!")

    def set_mining_time(self):
        # Festgelegte Zeiten – in einem echten Spiel wären dies z. B. 20s bei Holz, 8s bei Stein etc.
        # Hier wird jedoch ein Faktor 1/10 verwendet, um das Testen zu erleichtern.
        if self.level_names[self.level] == "Holz":
            self.mining_time = 20  # Sekunden
        elif self.level_names[self.level] == "Stein":
            self.mining_time = 8  # Sekunden
        else:
            # Für höhere Stufen ein Standardwert
            self.mining_time = 5  # Sekunden

    def __str__(self):
        return f"{self.level_names[self.level]} Spitzhacke"

# -----------------------------
# Klasse Spieler
# Der Spieler hat einen Namen, ein Inventar, eine Spitzhacke und befindet sich zu Beginn in der Kohlenmine.
# Er kann aktiv Kohle abbauen.
# -----------------------------
class Spieler:
    def __init__(self, name):
        self.name = name
        self.inventar = Inventar()
        self.spitzhacke = Spitzhacke()
        # self.location = "Kohlenmine"
        self.money = 0  # Währung の (Rwo)

    def mine_coal(self):
        if self.inventar.total_items() < self.inventar.max_slots * self.inventar.max_per_slot:
            print(f"\n{self.name} schwingt die {self.spitzhacke} und versucht Kohle abzubauen...")
            # Simuliere den Abbauprozess:
            simulated_time = self.spitzhacke.mining_time / 10  # Beschleunigte Zeit für Demo-Zwecke
            time.sleep(simulated_time) # set to 'self.spitzhacke.mining_time' for real time
            if self.inventar.add_item("Kohle", 1):
                print("1 Kohle wurde abgebaut.")
            else:
                print("Kohle konnte nicht ins Inventar aufgenommen werden.")
        else:
            print("Inventar ist voll!")

    def mine_material(self, material: str, anzahl: int = 1):
        # Simuliere verschiedene Abbauzeiten je nach Material
        mining_times = {
            "kohle": self.spitzhacke.mining_time / 10,
            "roheisen": max(self.spitzhacke.mining_time / 8, 0.5),
        }
        mat = material.lower()
        if mat not in mining_times:
            print(f"{material} kann hier nicht abgebaut werden.")
            return
        max_moeglich = (self.inventar.max_slots * self.inventar.max_per_slot) - self.inventar.total_items()
        if max_moeglich <= 0:
            print("Inventar ist voll!")
            return
        if anzahl is None or anzahl > max_moeglich:
            anzahl = max_moeglich
        if anzahl <= 0:
            print("Kein Platz im Inventar!")
            return
        print(f"\n{self.name} schwingt die {self.spitzhacke} und versucht {anzahl}x {material} abzubauen...")
        time.sleep(mining_times[mat] * anzahl)
        hinzugefügt = self.inventar.add_item(material.capitalize(), anzahl)
        if hinzugefügt:
            print(f"{anzahl} {material.capitalize()} wurden abgebaut.")
        else:
            print(f"Nicht alles konnte ins Inventar aufgenommen werden.")

# -----------------------------
# Klasse Gustaf (Verarbeiter)
# Mit Gustaf werden 15 Kohle in 15 Hartkohle umgewandelt.
# -----------------------------
class Gustaf:
    def __init__(self):
        self.name = "Gustaf der Verarbeiter"
        self.rezepte = self.lade_rezepte()

    def lade_rezepte(self):
        try:
            with open("rezepte.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Rezepte: {e}")
            return {}

    def verarbeite(self, spieler: 'Spieler', material: str, anzahl: int = 1):
        rezept = self.rezepte.get(material.capitalize())
        if not rezept:
            print(f"Kein Rezept für {material} gefunden.")
            return
        # Prüfe, wie oft das Rezept maximal ausgeführt werden kann
        max_machbar = float('inf')
        for inp in rezept["input"]:
            vorrat = spieler.inventar.total_items_of(inp["material"])
            max_machbar = min(max_machbar, vorrat // inp["amount"])
        if max_machbar == 0:
            print("Nicht genügend Materialien für die Verarbeitung.")
            return
        if anzahl is None or anzahl > max_machbar:
            anzahl = max_machbar
        # Entferne Input-Materialien
        for inp in rezept["input"]:
            if not spieler.inventar.remove_item(inp["material"], inp["amount"] * anzahl):
                print(f"Nicht genügend {inp['material']} für die Verarbeitung.")
                return
        # Füge Output-Materialien hinzu
        success = True
        for out in rezept["output"]:
            if not spieler.inventar.add_item(out["material"], out["amount"] * anzahl):
                success = False
                break
        if success:
            print(f"Gustaf hat {anzahl}x {material} verarbeitet.")
        else:
            # Rückgängig machen, falls kein Platz
            for inp in rezept["input"]:
                spieler.inventar.add_item(inp["material"], inp["amount"] * anzahl)
            for out in rezept["output"]:
                spieler.inventar.remove_item(out["material"], out["amount"] * anzahl)
            print("Kein Platz im Inventar für das Ergebnis!")

class Anton:
    def __init__(self):
        self.name = "Anton der Aufwerter"

    def upgrade_pickaxe(self, spieler: Spieler):
        if spieler.spitzhacke.level == 0:
            if spieler.inventar.has_item("Hartkohle", 2):
                spieler.inventar.remove_item("Hartkohle", 2)
                spieler.spitzhacke.upgrade()
                print("Anton hat die Spitzhacke auf Stein aufgewertet.")
            else:
                print("Nicht genügend Hartkohle, um die Spitzhacke aufzuwerten.")
        else:
            print("Die Spitzhacke ist bereits aufgewertet oder ein Upgrade ist nicht verfügbar.")

class Vincent:
    def __init__(self):
        self.name = "Vincent der Verkäufer"
    
    def erstelle_antiquitaet(self, spieler: Spieler):
        if spieler.inventar.has_item("Hartkohle", 1):
            spieler.inventar.remove_item("Hartkohle", 1)
            antiquitaet = Antiquitaet()
            if spieler.inventar.add_item(antiquitaet.name, 1):
                print(f"Vincent hat eine Antiquität '{antiquitaet.name}' erzeugt!")
            else:
                print("Kein Platz im Inventar für die Antiquität!")
        else:
            print("Nicht genügend Hartkohle, um eine Antiquität herzustellen.")

class Antiquitaet:
    def __init__(self):
        self.name = self.generate_name()

    def generate_name(self):
        rarities = ["gewöhnlich", "selten", "sehr selten"]
        rarity = random.choice(rarities)
        return f"Antiquität ({rarity})"

    def __str__(self):
        return self.name
    
# -----------------------------
# Hilfsfunktionen
def print_help():
    print("\nVerfügbare Befehle:")
    print("  abbauen <material> <anzahl> - Baue eine bestimmte Anzahl des angegebenen Materials ab (z.B. 'abbauen kohle 5').")
    print("  inventar            - Zeige dein aktuelles Inventar.")
    print("  status              - Zeige deinen Status (Standort, Spitzhacke, Inventar).")
    print("  verarbeite <mat> <anzahl> - Lasse Gustaf Material nach Rezept verarbeiten (z.B. 'verarbeite roheisen 2').")
    print("  upgrade             - Lasse Anton deine Spitzhacke (Holz) mit 2 Hartkohle auf Stein upgraden.")
    print("  antiquitaet         - Lasse Vincent eine Antiquität herstellen (benötigt 1 Hartkohle).")
    print("  eisenmine           - Gehe mit 3 Hartkohle in die Eisenmine.")
    print("  help/hilfe          - Zeige dieses Hilfsmenü an.")
    print("  exit                - Beende das Spiel.\n")

# ASCII Art für den Titel
#  _____               _            __  __
# / _  / __ _ _ __ ___(_) __ _ _ __ \ \/ /
# \// / / _` | '__/ __| |/ _` | '_ \ \  / 
#  / //\ (_| | |  \__ \ | (_| | | | |/  \ 
# /____/\__,_|_|  |___/_|\__,_|_| |_/_/\_\

# Gradients:
# #FBC2EB -> #A6C1EE
# #5EA4FF -> #A7E06F 

ascii_art = " _____               _            __  __\n/ _  / __ _ _ __ ___(_) __ _ _ __ \\ \\/ /\n\\// / / _` | '__/ __| |/ _` | '_ \\ \\  /\n / //\\ (_| | |  \\__ \\ | (_| | | | |/  \\ \n/____/\\__,_|_|  |___/_|\\__,_|_| |_/_/\\_\\"

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

def interpolate_color_multi(colors: list[tuple[int, int, int]], factor: float) -> tuple[int, int, int]:
    if factor <= 0: return colors[0]
    if factor >= 1: return colors[-1]

    total_segments = len(colors) - 1
    scaled = factor * total_segments
    index = int(scaled)
    inner_factor = scaled - index

    start_color = colors[index]
    end_color = colors[index + 1]
    return tuple(int(start + (end - start) * inner_factor) for start, end in zip(start_color, end_color))

def gradient_text(text: str, hex_colors: tuple[str], direction: str = "lr") -> str:
    if len(hex_colors) < 2:
        raise ValueError("At least two colors are required.")

    rgb_colors = [hex_to_rgb(h) for h in hex_colors]
    lines = text.splitlines()

    if direction in ("td", "bu"):
        reverse = direction == "bu"
        lines_proc = lines[::-1] if reverse else lines
        total = len(lines_proc) - 1 if len(lines_proc) > 1 else 1
        result_lines = []
        for i, line in enumerate(lines_proc):
            factor = i / total
            rgb = interpolate_color_multi(rgb_colors, factor)
            result_lines.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{line}\033[0m")
        return "\n".join(result_lines[::-1] if reverse else result_lines)

    elif direction in ("lr", "rl"):
        reverse = direction == "rl"
        result_lines = []
        for line in lines:
            chars = list(line)
            if reverse:
                chars = chars[::-1]
            total = len(chars) - 1 if len(chars) > 1 else 1
            line_out = []
            for i, char in enumerate(chars):
                factor = i / total
                rgb = interpolate_color_multi(rgb_colors, factor)
                line_out.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{char}")
            if reverse:
                line_out = line_out[::-1]
            result_lines.append("".join(line_out) + "\033[0m")
        return "\n".join(result_lines)
    
    else:
        raise ValueError("Direction must be one of: 'lr', 'rl', 'td', 'bu'")

def color_text(text: str, hex_color: str) -> str:
    rgb = hex_to_rgb(hex_color)
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"

# Unreadable text
def obfuscate_text(text: str) -> str:
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(charset) if c != ' ' else ' ' for c in text)

# print(gradient_text("Zars\nhallo\nP14a", ("#FBC2EB", "#A6C1EE"), "bu")) # !testing
# print(color_text("Zars\nhallo\nP14a", "#FBC2EB")) # !testing

# -----------------------------
# Hauptspiel-Schleife
# -----------------------------
def main():
    print(gradient_text(ascii_art, ("#FBC2EB", "#A6C1EE"), "lr"))
    name = input("\nWie soll dein Pionier heißen? # ")
    spieler = Spieler(name)
    gustaf = Gustaf()
    anton = Anton()
    vincent = Vincent()

    print(f"""\nWelcome on board pioneer {color_text(spieler.name, "#FBC2EB")}! We're approaching {gradient_text("Zars P14a", ("#FBC2EB", "#A6C1EE"), "lr")}.
The air is thin, the ground is rough – but you are ready. As one of the first settlers on this remote planet, it is up to you to tap into its resources and continuously improve your equipment.

Equipped with nothing more than a simple wooden pickaxe, you begin your adventure. Deep beneath the surface, coal, iron ore, and more await – ready to be discovered by you.

Use the commands at your disposal to mine resources, have them processed by Gustaf, upgrade your pickaxe with Anton, or create mysterious antiquities with Vincent. If you have enough hard coal, you can even enter the dangerous iron mine.

Type '{color_text("help", "#A7E06F")}' to see all available commands.
Your mission begins now. Good luck, {color_text(spieler.name, "#FBC2EB")}.\n""")
    while True:
        command = input("What do you want to do, pioneer? (type 'help' for the help menu): ").strip().lower()
        if command in ["exit"]:
            print(f"\nMemory encrypted!\nPlanet {gradient_text("Zars P14a", ("#FBC2EB", "#A6C1EE"))} is waiting for you to return.\n\nData(Player(\"{spieler.name}\")): [\n\t{obfuscate_text("ashdih askdhaiwuihh asiudhwudbn asdhkjhwih aksjdhdwi")}\n]\n")
            break
        elif command in ["help", "hilfe"]:
            print_help()
        elif command.startswith("abbauen"):
            parts = command.split()
            if len(parts) >= 2:
                material = parts[1]
                anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                spieler.mine_material(material, anzahl)
            else:
                print("Pioneer! Provide a material, e.g. 'mine coal' or with a count 'mine coal 5'.")
        elif command == "inventar":
            print("Current inventory:", spieler.inventar)
        elif command == "status":
            print(f"\nPlayer: {spieler.name}")
            print(f"Location: {spieler.location}")
            print(f"Pickaxe: {spieler.spitzhacke}")
            print("Inventory:", spieler.inventar, "\n")
        elif command.startswith("verarbeite"):
            parts = command.split()
            if len(parts) >= 2:
                material = parts[1]
                anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                gustaf.verarbeite(spieler, material, anzahl)
            else:
                print("Pioneer! Provide a material, e.g. 'process raw_iron 2'.")
        elif command == "upgrade":
            anton.upgrade_pickaxe(spieler)
        elif command == "antiquitaet":
            vincent.erstelle_antiquitaet(spieler)
        else:
            print("Pioneer! We don't know this one. Please type 'help' to see the available commands.")

# Start the game
main()