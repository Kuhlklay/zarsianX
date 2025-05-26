import time
import random
# import asyncio
import json
import string

class Inventory:
    def __init__(self, owner=None):
        self.owner = owner
        # Every slot is a Dictionary with "item" and "count"
        self.slots = []
        self.max_slots = 5
        self.max_per_slot = 20

    def add_item(self, item, quantity=1):
        # Try to use existing stacks to fill up
        for slot in self.slots:
            if slot["item"] == item and slot["count"] < self.max_per_slot:
                space = self.max_per_slot - slot["count"]
                add_here = min(space, quantity)
                slot["count"] += add_here
                quantity -= add_here
                if quantity == 0:
                    return True
        # If quantity is remaining, add new slots – if there is still space in the inventory
        while quantity > 0:
            if len(self.slots) < self.max_slots:
                add_here = min(self.max_per_slot, quantity)
                self.slots.append({"item": item, "count": add_here})
                quantity -= add_here
            else:
                print(color_text(f"Not enough free space in inventory for {item}!", "#FF6961"))
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
            print(color_text(f"Not enough {item} to remove!", "#FF6961"))
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
            return "Inventory is empty."
        output = "\n╔════════════════╦════════╗\n"
        output += "║ Item           ║ Amount ║\n"
        output += "╠════════════════╬════════╣\n"
        for slot in self.slots:
            output += f"║ {slot['item']:<14} ║ {slot['count']:>5}x ║\n"
        output += "╚════════════════╩════════╝"
        output += f"\nTotal: {self.total_items()} Items"
        output += f"\nRwo: {self.owner.money}"
        return output

class Pickaxe:
    def __init__(self):
        self.level_names = ["Wood", "Stone", "Iron", "Gold", "Diamond"]
        self.level = 3  # Start: Wood = 0
        self.set_mining_time()

    def upgrade(self):
        if self.level < len(self.level_names) - 1:
            self.level += 1
            self.set_mining_time()
            print(f"Pickaxe upgraded to {self.level_names[self.level]}!")
        else:
            print("Maximum upgrade level reached!")

    def set_mining_time(self):
        # TODO: fetch from JSON file
        # Festgelegte Zeiten – in einem echten Spiel wären dies z. B. 20s bei Wood, 8s bei Stone etc.
        # Hier wird jedoch ein Faktor 1/10 verwendet, um das Testen zu erleichtern.
        if self.level_names[self.level] == "Wood":
            self.mining_time = 2  # Sekunden
        elif self.level_names[self.level] == "Stone":
            self.mining_time = 1.6  # Sekunden
        else:
            # Für höhere Stufen ein Standardwert
            self.mining_time = 2  # Sekunden

    def __str__(self):
        return f"{self.level_names[self.level]} Pickaxe"

class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = Inventory(owner=self)
        self.pickaxe = Pickaxe()
        self.money = 0  # Währung の (Rwo)

        with open("mining.json", "r") as f:
            global mining_data
            mining_data = json.load(f)

    def mine(self, material: str, amount: int = 1):
        mat = material.lower()
        
        if mat not in mining_data:
            print(f"{material} can't be mined because it does not exist.")
            return

        data = mining_data[mat]
        
        # Check ob Pickaxe-Level ausreicht
        if self.pickaxe.level < data["mining_level"]:
            print(color_text(f"Your pickaxe is too weak to mine {material}.", "#FF6961"))
            return

        # Verfügbare Inventar-Kapazität prüfen
        max_moeglich = (self.inventory.max_slots * self.inventory.max_per_slot) - self.inventory.total_items()
        if max_moeglich <= 0:
            print(color_text("Inventory is full!", "#FF6961"))
            return

        if amount is None or amount > max_moeglich:
            amount = max_moeglich
        if amount <= 0:
            print(color_text("No space in inventory!", "#FF6961"))
            return

        print(f"\n{self.name} is using a {self.pickaxe} trying to mine {amount}x {material}...")

        # Mining-Zeit basierend auf Material und Menge
        total_time = data["mining_time"] * amount * self.pickaxe.mining_time
        time.sleep(total_time)

        total_obtained = 0
        for _ in range(amount):
            drops = data["drop_rates"]
            current = drops["min"]
            chance = drops["rate"]
            # Berechne zusätzlichen Drop basierend auf der Rate
            while current < drops["max"]:
                if random.random() <= chance:
                    current += 1
                else:
                    break
            total_obtained += current

        hinzugefügt = self.inventory.add_item(data["output"], total_obtained)

        if hinzugefügt:
            print(f"You've mined {amount}x {material} and received {total_obtained}x {data['output']}.")
        else:
            print(color_text("Not all items could be added to the inventory.", "#FF6961"))
            
    def has_money(self, amount):
        return self.money >= amount
    
    def add_money(self, amount):
        self.money += amount
        print(f"Added {amount} (Rwo) to your account. Total: {self.money} (Rwo)")

    def remove_money(self, amount):
        if self.has_money(amount):
            self.money -= amount
            print(f"Removed {amount} (Rwo) from your account. Total: {self.money} (Rwo)")
        else:
            print(color_text(f"Not enough money! You have only {self.money} (Rwo).", "#FF6961"))

class Processor:
    def __init__(self):
        self.name = "Gustaf der Verarbeiter"
        self.recipes = self.load_json()

    def load_json(self):
        try:
            with open("recipes.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(color_text(f"Error while loading recipes: {e}", "#FF6961"))
            return {}

    def process(self, player: Player, material: str, amount: int = 1):
        recipe = self.recipes.get(material.capitalize())
        if not recipe:
            print(color_text(f"No recipe found for {material}.", "#FF6961"))
            return
        # Prüfe, wie oft das Rezept maximal ausgeführt werden kann
        max_machbar = float('inf')
        for inp in recipe["input"]:
            vorrat = player.inventory.total_items_of(inp["material"])
            max_machbar = min(max_machbar, vorrat // inp["amount"])
        if max_machbar == 0:
            print(color_text("Not enough materials for processing.", "#FF6961"))
            return
        if amount is None or amount > max_machbar:
            amount = max_machbar
        # Entferne Input-Materialien
        for inp in recipe["input"]:
            if not player.inventory.remove_item(inp["material"], inp["amount"] * amount):
                print(color_text(f"Not enough {inp['material']} for processing.", "#FF6961"))
                return
        # Füge Output-Materialien hinzu
        success = True
        for out in recipe["output"]:
            if not player.inventory.add_item(out["material"], out["amount"] * amount):
                success = False
                break
        if success:
            print(f"Gustaf hat {amount}x {material} verarbeitet.")
        else:
            # Rückgängig machen, falls kein Platz
            for inp in recipe["input"]:
                player.inventory.add_item(inp["material"], inp["amount"] * amount)
            for out in recipe["output"]:
                player.inventory.remove_item(out["material"], out["amount"] * amount)
            print(color_text("No room in inventory for the result!", "#FF6961"))

class Upgrader:
    def __init__(self):
        self.name = "Anton der Aufwerter"

    def upgrade_pickaxe(self, player: Player):
        if player.pickaxe.level == 0:
            if player.inventory.has_item("Hartkohle", 2):
                player.inventory.remove_item("Hartkohle", 2)
                player.pickaxe.upgrade()
                print("Anton hat die Pickaxe auf Stone aufgewertet.")
            else:
                print("Nicht genügend Hartkohle, um die Pickaxe aufzuwerten.")
        else:
            print("Die Pickaxe ist bereits aufgewertet oder ein Upgrade ist nicht verfügbar.")

class Bizman: # short for Businessman
    def __init__(self):
        self.name = "Bizman"

    def create_antiquity(self, player: Player):
        if player.inventory.has_item("Hartkohle", 1):
            player.inventory.remove_item("hard_coal", 1)
            antiquity = Antiquity()
            if player.inventory.add_item(antiquity.name, 1):
                print(f"Bizman forged a '{antiquity.name}'!")
            else:
                print(color_text("There's no room in your backpack for this antiquity!", "#FF6961"))
        else:
            print(color_text("Not enough coal to create an antiquity.", "#FF6961"))

class Antiquity:
    def __init__(self):
        self.name = self.generate_name()

    def generate_name(self):
        rarities = ["common", "uncommon", "rare", "epic", "legendary"]
        rarity = random.choice(rarities)
        return f"Antiquity ({rarity})"

    def __str__(self):
        return self.name
    
# -----------------------------
# Helper functions
def print_help():
    #dynamic way to print all the commands with accurate spacing to the longest command
    commands = [
        ("mine <material> <amount>", "Mine a specific amount of the specified material (e.g. 'mine coal 5')."),
        ("inventory", "Show your current inventory."),
        ("status", "Show your status (location, pickaxe, inventory)."),
        ("process <recipe> <amount>", "Let Gustaf process material according to the recipe (e.g. 'process raw_iron 2')."),
        ("upgrade", "Let Upgrader upgrade your pickaxe (wood) to stone with 2 hard coal."),
        ("antiquity", "Let Bizman create an antiquity (requires 1 hard coal)."),
        ("help", "Show this help menu."),
        ("exit", "Exit the game.")
    ]

    # gets all the lengths of the commands and finds the longest one to make the spacing dynamic
    max_length = max(len(command[0]) for command in commands) + 2
    print("\nAvailable commands:")
    for command, description in commands:
        print(f"  {command:<{max_length}} - {description}")
    print("\n")

# Gradients:
# #FBC2EB -> #A6C1EE
# #5EA4FF -> #A7E06F 

#   _____               _            __  __
# / _  / __ _ _ __ ___(_) __ _ _ __ \\ \\/ /
# \\// / / _` | '__/ __| |/ _` | '_ \\ \\  /
#  / //\\ (_| | |  \__ \\ | (_| | | | |/  \\
# /____/\\__,_|_|  |___/_|\\__,_|_| |_/_/\\_\\

ascii_art_logo = """
 
███████╗░█████╗░██████╗░░██████╗██╗░█████╗░███╗░░██╗░██╗░░██╗
╚════██║██╔══██╗██╔══██╗██╔════╝██║██╔══██╗████╗░██║░╚██╗██╔╝
░░███╔═╝███████║██████╔╝╚█████╗░██║███████║██╔██╗██║░░╚███╔╝░
██╔══╝░░██╔══██║██╔══██╗░╚═══██╗██║██╔══██║██║╚████║░░██╔██╗░
███████╗██║░░██║██║░░██║██████╔╝██║██║░░██║██║░╚███║░██╔╝╚██╗
╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝░╚═╝░░╚═╝
"""

ascii_art_planet = """
                                        _.oo.,
                 _.u[[/;:,.         .odMMMMMM'
              .o888UU[[[/;:-.  .o@P^    MMM^
             oN88888UU[[[/;::-.        dP^
            dNMMNN888UU[[[/;:--.   .o@P^
           MMMMMNN888UU[[/;::-. o@^
           NNMMMNN888UU[[[/~.o@P^
           888888888UU[[[/o@^-..
          oI8888UU[[[/o@P^:--..
       .@^  YUU[[[/o@^;::---..
     oMP^    ^/o@P^;:::---..
  .dMMM    .o@^ ^;::---...
 dMMMMMMM@^ˋ       ˋ^^^^
YMMMU@^
 ^^
"""

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
# Main Game Loop
# -----------------------------
def main():
    print(gradient_text(ascii_art_logo, ("#FBC2EB", "#A6C1EE"), "lr"))
    name = input("\nWhat's your name again? # ")
    player = Player(name)
    gustaf = Processor()
    anton = Upgrader()
    vincent = Bizman()

    print(gradient_text(ascii_art_planet ,("#E4BDD4", "#4839A1"), "td"))
    print(f"""\nWelcome on board of the {gradient_text("ZarsianX", ("#E4BDD4", "#4839A1"), "lr")}, pioneer {color_text(player.name, "#FBC2EB")}! We're approaching {gradient_text("Zars P14a", ("#FBC2EB", "#A6C1EE"), "lr")}.
The air is thin, the ground is rough – but you are ready. As one of the first settlers on this remote planet, it is up to you to tap into its resources and continuously improve your equipment.

Equipped with nothing more than a simple wooden pickaxe, you begin your adventure. Deep beneath the surface, coal, iron ore, and more await – ready to be discovered by you.

Use the commands at your disposal to mine resources, have them processed by Gustaf, upgrade your pickaxe with Anton, or create mysterious antiquities with Vincent. If you have enough hard coal, you can even enter the dangerous iron mine.

Initiating planetfall! Deploying parachute... Skipping parachute... Skipping parachute...! Sk.. i.. {obfuscate_text("ipping parachute!")}...
Planetfall achieved! Now it's your turn...

Pioneer acceptable! Toolbox opened!
          
Type '{color_text("help", "#A7E06F")}' to see all available commands.

Good luck, {color_text(player.name, "#FBC2EB")}.
- And remember: Humanity counts on you!\n""")
    while True:
        command = input("What do you want to do, pioneer? # ").strip().lower()
        if command in ["exit"]:
            print(f"\nMemory encrypted!\nPlanet {gradient_text("Zars P14a", ("#FBC2EB", "#A6C1EE"))} is waiting for you to return.\n\nData(Player(\"{player.name}\")): [\n\t{obfuscate_text("ashdih askdhaiwuihh asiudhwudbn asdhkjhwih aksjdhdwi")}\n]\n")
            break
        elif command in ["help"]:
            print_help()
        elif command.startswith("mine"):
            parts = command.split()
            if len(parts) >= 2:
                material = parts[1]
                anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                player.mine(material, anzahl)
            else:
                print("Pioneer! Provide a material, e.g. 'mine coal' or with a count 'mine coal 5'.")
        elif command == "inventory":
            print("Current inventory:", player.inventory)
        elif command == "status":
            print(f"\nPlayer: {player.name}")
            print(f"Pickaxe: {player.pickaxe}")
            print("Inventory:", player.inventory, "\n")
        elif command.startswith("process"):
            parts = command.split()
            if len(parts) >= 2:
                material = parts[1]
                anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                gustaf.process(player, material, anzahl)
            else:
                print("Pioneer! Provide a material, e.g. 'process iron'.")
        elif command == "upgrade":
            anton.upgrade_pickaxe(player)
        elif command == "antiquity":
            vincent.create_antiquity(player)
        else:
            print("Pioneer! We don't know this one. Please type 'help' to see the available commands.")

# Start the game
main()