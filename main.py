import difflib
import time
import random
import string
from enum import Enum
from registry import *

class LogLevel(Enum):
    ERROR = {"color": "#FF6961", "symbol": "⊘"}
    WARNING = {"color": "#FFB561", "symbol": "⊜"}
    TIP = {"color": "#6A7EAC", "symbol": "⊙"}
    
def log(message: str, level: LogLevel) -> str:
    color = level.value["color"]
    symbol = level.value["symbol"]
    return f"{colorText(symbol, color)} {message}"

class Inventory:
    def __init__(self, owner=None):
        self.owner = owner
        # Every slot is a Dictionary with "item" and "count"
        self.slots = []
        self.maxSlots = 16
        self.stack = 32

    def addItem(self, item: Item, quantity=1):
        # Try to use existing stacks to fill up
        for slot in self.slots:
            if slot["item"] == item and slot["count"] < self.stack:
                space = self.stack - slot["count"]
                add = min(space, quantity)
                slot["count"] += add
                quantity -= add
                if quantity == 0:
                    return True
        # If quantity is remaining, add new slots – if there is still space in the inventory
        while quantity > 0:
            if len(self.slots) < self.maxSlots:
                add = min(self.stack, quantity)
                self.slots.append({"item": item, "count": add})
                quantity -= add
            else:
                print(log(f"Not enough free space in inventory for {item}!", LogLevel.WARNING))
                return False
        return True

    def removeItem(self, item: Item, quantity=1):
        removed = 0
        for slot in self.slots:
            if slot["item"] == item:
                canRemove = min(slot["count"], quantity - removed)
                slot["count"] -= canRemove
                removed += canRemove
        # Leere Slots entfernen
        self.slots = [slot for slot in self.slots if slot["count"] > 0]
        if removed < quantity:
            print(log(f"Not enough {item} to remove!", LogLevel.WARNING))
            return False
        return True

    def totalItemsOf(self, item: Item):
        total = 0
        for slot in self.slots:
            if slot["item"] == item:
                total += slot["count"]
        return total

    def totalItems(self):
        return sum(slot["count"] for slot in self.slots)

    def hasItem(self, item: Item, quantity=1):
        return self.totalItemsOf(item) >= quantity

    def __str__(self):
        if not self.slots:
            print()
            return log("Inventory is empty!\n", LogLevel.WARNING)
        output = "\n╭───────────────────────────┬────────╮\n"
        output += "│ Item                      │ Amount │\n"
        output += "├───────────────────────────┼────────┤\n"
        for slot in self.slots:
            output += f"│ {slot['item'].name:<25} │ {slot['count']:>5}x │\n"
        output += "├─────────────┬─────────────┴────────┤\n"
        output += f"│ Total Items │ {self.totalItems():>20} │\n"
        output += f"│ Money       │ {(self.owner.displayMoney() if self.owner else 'N/A'):>20} │\n"
        output += "╰─────────────┴──────────────────────╯"
        return output

#class Pickaxe:
#    def __init__(self):
#        self.level = 0
#
#    def upgrade(self):
#        if self.level < 4:
#            self.level += 1
#            print(f"Pickaxe upgraded to {self.level_names[self.level]}!")
#        else:
#            print(log("Maximum upgrade level reached!", LogLevel.WARNING))
#
#    def __str__(self):
#        return f"{self.level_names[self.level]} Pickaxe"

class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = Inventory(owner=self)
        self.pickaxe = Tool.get("test_tool")  # Start with a test tool
        self.money = 0  # Währung の (Rwo)

    def mine(self, material: str, amount: int = 1):
        block = Block.get(material.lower())

        if not block:
            print(log(f"Can not mine {block.name} because it does not exist.", LogLevel.WARNING))
            return

        # Check ob Pickaxe-Level ausreicht
        if self.pickaxe.miningLevel < block.miningLevel:
            print(log(f"Your pickaxe is too weak to mine {block.name}.", LogLevel.WARNING))
            return

        # Verfügbare Inventar-Kapazität prüfen
        possible = (self.inventory.maxSlots * self.inventory.stack) - self.inventory.totalItems()
        if possible <= 0:
            print(log("Inventory is full!", LogLevel.WARNING))
            return

        if amount is None or amount > possible:
            amount = possible
        if amount <= 0:
            print(log("No space in inventory!", LogLevel.WARNING))
            return

        print(f"\n{colorText(self.name, '#6A7EAC')} is using a {self.pickaxe.name} trying to mine {amount}x {block.name}...")

        # Mining-Zeit basierend auf Material und Menge
        totalTime = block.miningTime * amount / self.pickaxe.timeFac
        time.sleep(totalTime)

        total = 0
        for _ in range(amount):
            drops = block.dropRates
            _min = drops.getRateFor(DropRateEnum.MIN)
            _max = drops.getRateFor(DropRateEnum.MAX)
            #print(f"Drops for {block.name}: {_min}x (min), {_max}x (max), rate: {drops.getRateFor(DropRateEnum.RATE)}")
            # Berechne zusätzlichen Drop basierend auf der Rate
            while _min < _max:
                if random.random() <= drops.getRateFor(DropRateEnum.RATE):
                    _min += 1
                else:
                    break
            total += _min

        added = self.inventory.addItem(block.dropItem, total)

        if added:
            print(f"You've mined {amount}x {block.name} and received {total}x {block.dropItem.name}.\n")
        else:
            print(colorText("Not all items could be added to the inventory.", "#FF6961"))
            print(colorText("Go clean it up.\n", "#FF6961"))

    def hasMoney(self, amount):
        return self.money >= amount

    def addMoney(self, amount):
        self.money += amount
        print(f"Added {self.displayMoney()} to your account. Total: {self.money} (Rwo)")

    def removeMoney(self, amount):
        if self.hasMoney(amount):
            self.money -= amount
            print(f"Removed {self.displayMoney()} from your account. Total: {self.money} (Rwo)")
        else:
            print(log(f"Not enough money! You have only {self.displayMoney()}.", LogLevel.WARNING))

    def displayMoney(self):
        return f"{self.money}⍹ (Wro)"

class Processor:
    def __init__(self):
        self.name = "Gustavu the Processor"

    def process(self, player: Player, recipe: Recipe, amount: int = 1):
        if not recipe:
            print(log(f"No recipe found for {recipe}.", LogLevel.WARNING))
            return
        
        # Prüfe, wie oft das Rezept maximal ausgeführt werden kann
        possible = float('inf')
        for inp in recipe.inputs:
            available = player.inventory.totalItemsOf(inp[0])
            print(f"Checking {inp[0].name}: max {available} available, {inp[1]} required per unit.")
            if available < inp[1]:
                print(log(f"Not enough {inp[0]} for processing.", LogLevel.WARNING))
                return
            possible = min(possible, available // inp[1])
        
        if possible == 0:
            print(log("Not enough materials for processing.", LogLevel.WARNING))
            return
        
        # Handle amount: default to 1 if None, reject if < 1, cap if > possible
        if amount is None:
            amount = 1
        if amount < 1:
            print(log("Amount must be at least 1.", LogLevel.WARNING))
            return
        if amount > possible:
            print(log(f"Cannot process {amount}x {recipe.ID}. Only {possible} possible due to limited materials.", LogLevel.WARNING))
            return
        
        # Entferne Input-Materialien
        for inp in recipe.inputs:
            if not player.inventory.removeItem(inp[0], inp[1] * amount):
                print(log(f"Not enough {inp[0]} for processing.", LogLevel.WARNING))
                return
        
        # Füge Output-Materialien hinzu
        success = True
        for out in recipe.outputs:
            if not player.inventory.addItem(out[0], out[1] * amount):
                success = False
                break
        
        if success:
            print(f"Gustavu has processed {amount}x {recipe.ID} successfully!")
        else:
            # Rückgängig machen, falls kein Platz
            for inp in recipe.inputs:
                player.inventory.addItem(inp[0], inp[1] * amount)
            for out in recipe.outputs:
                player.inventory.removeItem(out[0], out[1] * amount)
            print(colorText("No room in inventory for the result!", "#FF6961"))

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
                print(colorText("There's no room in your backpack for this antiquity!", "#FF6961"))
        else:
            print(colorText("Not enough coal to create an antiquity.", "#FF6961"))

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

def wordWrap(text: str, n: int = 50) -> list[str]:
    words = text.split()
    lines = []
    current = ""

    for word in words:
        # Prüfe, ob das Hinzufügen des nächsten Wortes die Zeile überschreiten würde
        if len(current) + len(word) + (1 if current else 0) > n:
            lines.append(current)
            current = word
        else:
            current += (" " if current else "") + word
    if current:
        lines.append(current)
    return lines

def printHelp():
    #dynamic way to print all the commands with accurate spacing to the longest command
    commands = [
        ("last", [(None, "Execute the last command again (excl. 'last', 'inventory', 'recipe', 'help' & 'exit')")]),
        ("mine", [("<material> <amount>?1", "Mine a material of additional count (e.g. '... coal 5')")]),
        ("inventory", [(None, "Show your current inventory")]),
        ("status", [(None, "Show your status (name, tool, inventory)")]),
        ("process", [("<recipe> <amount>?1", "Process material according to the recipe (e.g. '... iron_ingot 2')")]),
        ("recipe", [
            ("search <term>", "Search for a recipe name"),
            ("get|show <name>", "Get a recipe by name")
        ]),
        #("upgrade", "Let Upgrader upgrade your pickaxe (wood) to stone with 2 hard coal."),
        #("antiquity", "Let Bizman create an antiquity."),
        ("help", [(None, "Show this help menu")]),
        ("exit", [(None, "!! Exit the game")])
    ]

    # Descriptions for command per line is max. n Characters long
    # ╭─────────┬───────────────────────┬────────────────────────────────────────────────────────────────╮
    # │ Command │ Arguments             │ Description                                                    │
    # ├─────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
    # │ last    │ None                  │ Execute the last command again (not 'last', 'inventory',       │
    # │         │                       │ 'help' or 'exit')                                              │
    # ├─────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
    # │ mine    │ <material> <amount>?1 │ Mine a material of additional count (e.g. '... coal 5')        │ # '?' = optional with default value of '1'
    # ├─────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
    # │ recipe  │ search <term>         │ Search for a recipe name.                                      │
    # │         ├───────────────────────┼────────────────────────────────────────────────────────────────┤
    # │         │ get|show <name>       │ Get a recipe by name.                                          │
    # ╰─────────┴───────────────────────┴────────────────────────────────────────────────────────────────╯ # '|' = or

    # None-Type will be converted to "None" in the output
    # Prepare commands: flatten arguments, but only print each command once
    commands = [(cmd[0], [(arg[0] if arg[0] else "None", arg[1]) for arg in cmd[1]]) for cmd in commands]

    max_command_length = max(len(cmd[0]) for cmd in commands)
    max_arg_length = max(len(arg[0]) for cmd in commands for arg in cmd[1])
    max_desc_length = 50  # Max length for description

    print(log("'?' means optional value with default value e.g. 4", LogLevel.TIP))
    print(log("'|' means or / option", LogLevel.TIP))

    print("\n╭" + "─" * (max_command_length + 2) + "┬" + "─" * (max_arg_length + 2) + "┬" + "─" * (max_desc_length + 2) + "╮")
    print(f"│ {'Command':<{max_command_length}} │ {'Arguments':<{max_arg_length}} │ {'Description':<{max_desc_length}} │")
    print("├" + "─" * (max_command_length + 2) + "┼" + "─" * (max_arg_length + 2) + "┼" + "─" * (max_desc_length + 2) + "┤")

    for cmd in commands:
        command_name = cmd[0]
        args = cmd[1]
        for i, arg in enumerate(args):
            arg_text = arg[0]
            desc_text = arg[1]
            wrapped_desc = wordWrap(desc_text, max_desc_length)
            for j, line in enumerate(wrapped_desc):
                # Only print command name for the first argument/description
                if i == 0 and j == 0:
                    print(f"│ {command_name:<{max_command_length}} │ {arg_text:<{max_arg_length}} │ {line:<{max_desc_length}} │")
                elif j == 0:
                    print(f"│ {'':<{max_command_length}} │ {arg_text:<{max_arg_length}} │ {line:<{max_desc_length}} │")
                else:
                    print(f"│ {'':<{max_command_length}} │ {'':<{max_arg_length}} │ {line:<{max_desc_length}} │")
            # After first argument, don't print command name again
            if i < len(args) - 1:
                print(f"│ {'':<{max_command_length}} ├{'─' * (max_arg_length + 2)}┼{'─' * (max_desc_length + 2)}┤")
            command_name = ""
        # Print a separator line after each command's arguments/descriptions,
        # but only if this is not the last command in the list
        if cmd != commands[-1]:
            print("├" + "─" * (max_command_length + 2) + "┼" + "─" * (max_arg_length + 2) + "┼" + "─" * (max_desc_length + 2) + "┤")
    print("╰" + "─" * (max_command_length + 2) + "┴" + "─" * (max_arg_length + 2) + "┴" + "─" * (max_desc_length + 2) + "╯\n")

#╭─────────┬─────────────────────────────────────────╮
#│ Recipe  │ <name>                                  │
#├─────────┼──────────────────────────────┬──────────┤
#│ Inputs  │ <name>                       │ <amount> │ # 'Inputs' only shows the first input
#│         │ <name>                       │ <amount> │
#├─────────┼──────────────────────────────┼──────────┤
#│ Outputs │ <name>                       │ <amount> │ # 'Outputs' only shows the first output
#│         │ <name>                       │ <amount> │
#╰─────────┴──────────────────────────────┴──────────╯

def printRecipe(recipe: Recipe):
    print("\n╭─────────┬───────────────────────────────────────────────╮")
    print(f"│ {colorText("Recipe", '#A6C1EE')}  │ {recipe.ID:<45} │")
    print("├─────────┼────────────────────────────────────┬──────────┤")
    for item, qty in recipe.inputs:
        if item == recipe.inputs[0][0]: # makes 'Inputs' in first column only show the first input
            print(f"│ {colorText("Inputs", '#A6C1EE')}  │ {item.name:<34} │ {qty:>7}x │")
        else:
            print(f"│         │ {item.name:<34} │ {qty:>7}x │")
    print("├─────────┼────────────────────────────────────┼──────────┤")
    for item, qty in recipe.outputs:
        if item == recipe.outputs[0][0]: # makes 'Outputs' in first column only show the first output
            print(f"│ {colorText("Outputs", '#A6C1EE')} │ {item.name:<34} │ {qty:>7}x │")
        else:
            print(f"│         │ {item.name:<34} │ {qty:>7}x │")
    print("╰─────────┴────────────────────────────────────┴──────────╯\n")

# Gradients:
# #FBC2EB -> #A6C1EE
# #5EA4FF -> #A7E06F 

#   _____               _            __  __
# / _  / __ _ _ __ ___(_) __ _ _ __ \\ \\/ /
# \\// / / _` | '__/ __| |/ _` | '_ \\ \\  /
#  / //\\ (_| | |  \__ \\ | (_| | | | |/  \\
# /____/\\__,_|_|  |___/_|\\__,_|_| |_/_/\\_\\

asciiArtLogo = """

███████╗░█████╗░██████╗░░██████╗██╗░█████╗░███╗░░██╗░██╗░░██╗
╚════██║██╔══██╗██╔══██╗██╔════╝██║██╔══██╗████╗░██║░╚██╗██╔╝
░░███╔═╝███████║██████╔╝╚█████╗░██║███████║██╔██╗██║░░╚███╔╝░
██╔══╝░░██╔══██║██╔══██╗░╚═══██╗██║██╔══██║██║╚████║░░██╔██╗░
███████╗██║░░██║██║░░██║██████╔╝██║██║░░██║██║░╚███║░██╔╝╚██╗
╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝░╚═╝░░╚═╝
"""

asciiArtPlanet = """
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

def gradientText(text: str, hexColors: tuple[str], direction: str = "lr") -> str:
    if len(hexColors) < 2:
        raise ValueError("At least two colors are required.")

    rgb_colors = [hex_to_rgb(h) for h in hexColors]
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

def colorText(text: str, hex_color: str) -> str:
    rgb = hex_to_rgb(hex_color)
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"

# Unreadable text
def obfuscateText(text: str) -> str:
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(charset) if c != ' ' else ' ' for c in text)

# print(gradientText("Zars\nhallo\nP14a", ("#FBC2EB", "#A6C1EE"), "bu")) # !testing
# print(colorText("Zars\nhallo\nP14a", "#FBC2EB")) # !testing

# -----------------------------
# Main Game Loop
# -----------------------------
def main():
    print(gradientText(asciiArtLogo, ("#FBC2EB", "#A6C1EE"), "lr"))
    name = input("\nWhat's your name again? # ")
    player = Player(name)
    gustaf = Processor()
    anton = Upgrader()
    vincent = Bizman()

    print(gradientText(asciiArtPlanet ,("#E4BDD4", "#4839A1"), "td"))
    print(f"""
Welcome on board of the {gradientText("ZarsianX", ("#E4BDD4", "#4839A1"), "lr")}, pioneer {colorText(player.name, "#FBC2EB")}! We're approaching {gradientText("Zars P14a", ("#FBC2EB", "#A6C1EE"), "lr")}.
The air is thin, the ground is rough – but you are ready. As one of the first settlers on this remote planet, it is up to you to tap into its resources and continuously improve your equipment.

Equipped with nothing more than a simple tool, you begin your adventure. Deep beneath the surface, coal, iron ore, and more await – ready to be discovered by you.

Initiating planetfall!

Deploying parachute... 
Skipping parachute... Skipping parachute...! Sk.. i.. {obfuscateText("ipping parachute!")}...

Planetfall achieved! Now it's your turn...

Pioneer acceptable! 
Toolbox opened!

Type '{colorText("help", "#A7E06F")}' to see all available commands.

⌇ Good luck, {colorText(player.name, "#FBC2EB")}.
⌇ - And remember: Humanity counts on you!
""")
    while True:
        command = input("What do you want to do, pioneer? ⌗ ").strip().lower()
        if command not in ["last", "inventory", "recipe", "exit", "help"]:
            lastCommand = command  # Save the last command for "last" functionality

        if command == "last":
            if lastCommand:
                print(f"↶ Repeating last command: {lastCommand}")
                command = lastCommand
            else:
                print(log("No last command to repeat.", LogLevel.WARNING))
                continue

        parts = command.split()

        if command == "exit":
            print(f"\nMemory encrypted!\nPlanet {gradientText("Zars P14a", ("#FBC2EB", "#A6C1EE"))} is waiting for you to return.\n\nData(Player(\"{player.name}\")): [\n\t{obfuscateText("ashdih askdhaiwuihh asiudhwudbn asdhkjhwih aksjdhdwi")}\n]\n")
            break
        elif command == "help":
            printHelp()
        elif command.startswith("mine"):
            if len(parts) >= 2:
                material = parts[1]
                anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                player.mine(material, anzahl)
            else:
                print(log("Pioneer! Provide a material, e.g. 'mine coal' or with a count 'mine coal 5'.", LogLevel.WARNING))
        elif command == "inventory":
            print("Current inventory:", player.inventory)
        elif command == "status":
            print(f"\nName: {player.name}")
            print(f"Tool: {player.tool.name} (Level {player.tool.level})")
            print("Inventory:", player.inventory, "\n")
        elif command.startswith("process"):
            if len(parts) >= 2:
                recipe = Recipe.get(parts[1])
                anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                gustaf.process(player, recipe, anzahl)
            else:
                print(log("Pioneer! Provide a recipe name, e.g. 'process iron' or with a count 'process iron 5'.", LogLevel.WARNING))
        #elif command == "upgrade":
        #    anton.upgradeTool(player)
        #elif command == "antiquity":
        #    vincent.createAntiquity(player)
        elif command.startswith("recipe"):
            if len(parts) >= 3 and parts[1] == "search":
                searchTerm = " ".join(parts[2:])
                all_ids = list(Recipe.Registry.keys())
                # Fuzzy search mit difflib
                matches = difflib.get_close_matches(searchTerm, all_ids, n=10, cutoff=0.3)
                if matches:
                    maxLength = max(len(match) for match in matches)
                    print("\n╭" + "─" * (maxLength + 4) + "╮")
                    for rid in matches:
                        print(f"│ ∷ {rid:<{maxLength}} │")
                    print("╰" + "─" * (maxLength + 4) + "╯\n")
                else:
                    print()
                    print(log("No recipes found matching your search.\n", LogLevel.WARNING))
            elif len(parts) >= 3 and parts[1] in ["get", "show"]:
                recipeName = parts[2]
                recipe = Recipe.get(recipeName)
                if recipe:
                    printRecipe(recipe)
                else:
                    print(log(f"No recipe found with name '{recipeName}'.", LogLevel.WARNING))
            else:
                print(log("Usage: recipe search <name> or recipe get <name>", LogLevel.WARNING))
        else:
            print(log("Pioneer! We don't know this one. Please type 'help' to see the available commands.", LogLevel.ERROR))

# Start the game
main()