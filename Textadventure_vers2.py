import time
import random

# -----------------------------
# Klasse Inventar
# Das Inventar hat 3 Slots, wobei in jedem Slot maximal 5 gleiche Items gestapelt werden können.
# Somit sind insgesamt maximal 15 Items möglich.
# -----------------------------
class Inventar:
    def __init__(self):
        # Jeder Slot ist ein Dictionary mit "item" und "count"
        self.slots = []
        self.max_slots = 3
        self.max_per_slot = 50

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
        return str(self.slots)

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
        self.location = "Kohlenmine"

    def mine_coal(self):
        if self.inventar.total_items() < self.inventar.max_slots * self.inventar.max_per_slot:
            print(f"\n{self.name} schwingt die {self.spitzhacke} und versucht Kohle abzubauen...")
            # Simuliere den Abbauprozess:
            simulated_time = self.spitzhacke.mining_time  # Beschleunigte Zeit für Demo-Zwecke
            time.sleep(simulated_time)
            if self.inventar.add_item("Kohle", 1):
                print("1 Kohle wurde abgebaut.")
            else:
                print("Kohle konnte nicht ins Inventar aufgenommen werden.")
        else:
            print("Inventar ist voll!")

# -----------------------------
# Klasse Gustaf (Verarbeiter)
# Mit Gustaf werden 15 Kohle in 15 Hartkohle umgewandelt.
# -----------------------------
class Gustaf:
    def __init__(self):
        self.name = "Gustaf der Verarbeiter"

    def verarbeite_kohle(self, spieler: Spieler):
        if spieler.inventar.has_item("Kohle", 15):
            spieler.inventar.remove_item("Kohle", 15)
            spieler.inventar.add_item("Hartkohle", 15)
            print("Gustaf hat 15 Kohle in 15 Hartkohle verwandelt.")
        else:
            print("Nicht genügend Kohle für die Verarbeitung.")

# -----------------------------
# Klasse Anton (Aufwerter)
# Anton kann mit 2 Hartkohle die Holzspitzhacke (Stufe 0) auf eine Steinspitzhacke (Stufe 1) upgraden.
# -----------------------------
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

# -----------------------------
# Klasse Vincent (Verkäufer)
# Vincent verwendet 1 Hartkohle, um eine Antiquität herzustellen.
# Die Antiquität erhält eine zufällige Rarität von "gewöhnlich" bis "sehr selten".
# -----------------------------
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

# -----------------------------
# Klasse Antiquitaet
# Erzeugt eine Antiquität mit zufälliger Rarität.
# -----------------------------
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
# Hilfsmenü
# Zeigt alle verfügbaren Befehle an.
# -----------------------------
def print_help():
    print("\nVerfügbare Befehle:")
    print("  abbauen       - Baue manuell 1 Kohle ab.")
    print("  inventar     - Zeige dein aktuelles Inventar.")
    print("  status       - Zeige deinen Status (Standort, Spitzhacke, Inventar).")
    print("  verarbeite   - Lasse Gustaf 15 Kohle in 15 Hartkohle umwandeln (benötigt 15 Kohle).")
    print("  upgrade      - Lasse Anton deine Spitzhacke (Holz) mit 2 Hartkohle auf Stein upgraden.")
    print("  antiquitaet  - Lasse Vincent eine Antiquität herstellen (benötigt 1 Hartkohle).")
    print("  eisenmine    - Gehe mit 3 Hartkohle in die Eisenmine.")
    print("  help/hilfe   - Zeige dieses Hilfsmenü an.")
    print("  exit         - Beende das Spiel.\n")

# -----------------------------
# Hauptspielfunktion
# Der Spieler gibt seinen Namen ein und gelangt anschließend in eine interaktive Schleife,
# in der er über Befehle (inklusive Hilfe) agieren kann.
# -----------------------------
def main():
    print("Willkommen zum Kohlenminen-Abenteuer!")
    print("Anleitung:")
    print(" - Du startest mit einer Holzspitzhacke in der Kohlenmine.")
    print(" - Dein Inventar hat 3 Slots (jeweils bis zu 5 Items), also insgesamt 15 Items.")
    print(" - Baue manuell Kohle ab, indem du den Befehl 'abbauen' eingibst.")
    print(" - Sobald du 15 Kohle hast, kannst du zu Gustaf gehen, der Kohle in Hartkohle umwandelt.")
    print(" - Mit Hartkohle kannst du deine Spitzhacke upgraden, Antiquitäten herstellen oder in die Eisenmine gehen.\n")
    
    name = input("Bitte gib deinen Spielernamen ein: ")
    spieler = Spieler(name)
    gustaf = Gustaf()
    anton = Anton()
    vincent = Vincent()
    
    print_help()
    
    while True:
        command = input("Bitte gib einen Befehl ein (tippe 'help' für das Hilfsmenü): ").strip().lower()
        if command in ["exit"]:
            print("Spiel beendet. Danke fürs Spielen!")
            break
        elif command in ["help", "hilfe"]:
            print_help()
        elif command in ["abbauen", "mine"]:
            spieler.mine_coal()
        elif command in ["inventar"]:
            print("Aktuelles Inventar:", spieler.inventar)
        elif command in ["status"]:
            print(f"\nSpieler: {spieler.name}")
            print(f"Standort: {spieler.location}")
            print(f"Spitzhacke: {spieler.spitzhacke}")
            print("Inventar:", spieler.inventar, "\n")
        elif command in ["verarbeite"]:
            gustaf.verarbeite_kohle(spieler)
        elif command in ["upgrade"]:
            anton.upgrade_pickaxe(spieler)
        elif command in ["antiquitaet"]:
            vincent.erstelle_antiquitaet(spieler)
        elif command in ["eisenmine"]:
            if spieler.inventar.has_item("Hartkohle", 3):
                spieler.inventar.remove_item("Hartkohle", 3)
                spieler.location = "Eisenmine"
                print("Du hast 3 Hartkohle ausgegeben und betrittst die Eisenmine. Viel Erfolg!")
            else:
                print("Nicht genügend Hartkohle, um in die Eisenmine zu gelangen.")
        else:
            print("Unbekannter Befehl. Bitte tippe 'help', um die verfügbaren Befehle anzuzeigen.")

if __name__ == "__main__":
    main()
