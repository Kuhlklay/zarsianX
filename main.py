import difflib
import time
import random
import string
import copy
from enum import Enum
from registry import Item, Tool, Block, Recipe, DropRateEnum

def installPackages():
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.completion import WordCompleter, NestedCompleter
    except ImportError:
        print("📦 Required packages not found. Execute 'install-linux.sh' (linux) or 'install-windows.bat' (windows) to install them.")

class LogLevel(Enum):
    ERROR = {"color": "#FF6961", "symbol": "⊘"}
    WARNING = {"color": "#FFB561", "symbol": "⊜"}
    TIP = {"color": "#6A7EAC", "symbol": "⊙"}

def log(message: str, level: LogLevel) -> str:
    color = level.value["color"]
    symbol = level.value["symbol"]
    return f"{colorText(symbol + " " + message, color)}"

class Inventory:
    stack: int = 64

    def __init__(self, owner=None):
        self.owner = owner
        # Every slot is a Dictionary with "item" and "count"
        self.slots = []
        self.maxSlots = 36

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
        removed: int = 0
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
        total: int = 0
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

        sortedSlots = sorted(self.slots, key=lambda slot: slot["item"].name.lower())
        slotCount = len(sortedSlots)

        # Spaltenanzahl festlegen
        if slotCount <= 8:
            columns = 1
        elif slotCount <= 26:
            columns = 2
        else:
            columns = 3

        cWidth = 21  # column width
        aWidth = 6   # amount width
        ftWidth = 13 # footer titles width

        # Rahmenzeichen
        ctl = "╭"
        ctr = "╮"
        cbl = "╰"
        cbr = "╯"
        st = "┬"
        sl = "├"
        sr = "┤"
        sb = "┴"
        sm = "┼"
        lv = "│"
        lh = "─"

        # Rahmen-Zeilen bauen
        def bRow(left, mid, right):
            parts = []
            for _ in range(columns):
                parts.append(lh * (cWidth + 2) + mid + lh * (aWidth + 2))
            return f"{left}{mid.join(parts)}{right}\n"

        def cRow(items):
            row = lv
            for name, amount in items:
                row += f" {name:<{cWidth}} {lv} {amount:>{aWidth - 1}}x {lv}"
            for _ in range(columns - len(items)):
                row += f" {' ' * (cWidth)} {lv} {' ' * (aWidth)} {lv}"
            return row + "\n"

        def hRow():
            header = lv
            for _ in range(columns):
                header += f" {'Item':<{cWidth}} {lv} {'Amount':>{aWidth - 1}} {lv}"
            return header + "\n"

        output = "\n"
        output += bRow(ctl, st, ctr)
        output += hRow()
        output += bRow(sl, sm, sr)

        # Slots formatieren
        rows = []
        for i in range(0, slotCount, columns):
            group = []
            for j in range(columns):
                idx = i + j
                if idx < slotCount:
                    item = sortedSlots[idx]
                    group.append((item["item"].name, str(item["count"])))

            rows.append(cRow(group))
            
        output += "".join(rows)

        # Fußzeile
        tWidth = (cWidth + aWidth + 6) * columns + 1 # total width

        if columns == 1:
            output += f"{sl}{lh * ftWidth}{st}{lh * (cWidth + 2 - (ftWidth + 1))}{sb}{lh * (aWidth + 2)}{sr}\n"
        elif columns == 2:
            output += f"{sl}{lh * ftWidth}{st}{lh * (cWidth + 2 - (ftWidth + 1))}{sb}{lh * (aWidth + 2)}{sb}{lh * (cWidth + 2)}{sb}{lh * (aWidth + 2)}{sr}\n"
        else:
            output += f"{sl}{lh * ftWidth}{st}{lh * (cWidth + 2 - (ftWidth + 1))}{sb}{lh * (aWidth + 2)}{sb}"
            for _ in range(columns - 2):
                output += f"{lh * (cWidth + 2)}{sb}{lh * (aWidth + 2)}{sb}"

            output += f"{lh * (cWidth + 2)}{sb}{lh * (aWidth + 2)}{sr}\n"

        output += f"{lv} Total Items │ {self.totalItems():>{tWidth - 18}} {lv}\n"
        money_str = self.owner.displayMoney() if self.owner else "N/A"
        output += f"{lv} Money       │ {money_str:>{tWidth - 19}} {lv}\n"
        output += f"{cbl}{lh * ftWidth}{sb}{lh * (tWidth - 16)}{cbr}"

        return output

class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = Inventory(owner=self)
        if name == "test":
            self.tool = Tool.get("test_tool")  # Start with a test tool
        else:
            self.tool = Tool.get("wooden_pickaxe") # Start with a wooden pickaxe
        self.money = 0

    def mine(self, material: str, amount: int = 1):
        block = Block.get(material)

        if not block or not Block.exists(material):
            print(log(f"Unable to mine '{material}' because it's not scannable!", LogLevel.WARNING))
            return

        # Check ob Pickaxe-Level ausreicht
        if self.tool.miningLevel < block.miningLevel:
            print(log(f"Tool too weak to mine {block.ID}!", LogLevel.WARNING))
            return
        
        if amount > self.inventory.stack * 4:
            log("Why so much?", LogLevel.WARNING)

        total = 0
        for _ in range(amount):
            drops = block.dropRates
            _min = drops.getRateFor(DropRateEnum.MIN)
            _max = drops.getRateFor(DropRateEnum.MAX)
            #print(f"Drops for {block.ID}: {_min}x (min), {_max}x (max), rate: {drops.getRateFor(DropRateEnum.RATE)}")
            # Berechne zusätzlichen Drop basierend auf der Rate
            while _min < _max:
                if random.random() <= drops.getRateFor(DropRateEnum.RATE):
                    _min += 1
                else:
                    break
            total += _min

        # Verfügbare Inventar-Kapazität prüfen
        possible = (self.inventory.maxSlots * self.inventory.stack) - self.inventory.totalItems()
        if possible <= total:
            print(log("Inventory is full!", LogLevel.WARNING))
            return

        # Mining-Zeit basierend auf Material und Menge
        totalTime = block.miningTime * total / self.tool.timeFac
        print(f"\nTool: {self.tool.name}\nMining: {block.ID} ({amount}x)\nTime: ~{totalTime:.2f}s\n")

        time.sleep(totalTime)
        added = self.inventory.addItem(block.dropItem, total)

        if added:
            print(f"You've mined {amount}x {block.ID} and received {total}x {block.dropItem.name}.\n")
        else:
            print(log("Not all items could be added to the inventory.", LogLevel.WARNING))
            print(log("Go clean it up.\n", LogLevel.WARNING))

    def hasMoney(self, amount) -> bool:
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
        return f"{self.money}チ (Chi)"

class Processor:
    def process(self, player: Player, recipe: Recipe, amount: int = 1):
        if not recipe:
            print(log(f"No recipe found for {recipe}.", LogLevel.WARNING))
            return

        # 1. Prüfe maximal mögliche Ausführung
        possible = float('inf')
        for item, qty in recipe.inputs:
            available = player.inventory.totalItemsOf(item)
            print(f"Checking input {item.name}: {available} available, {qty} required per unit.")
            if available < qty:
                print(log(f"Not enough {item.name} for processing.", LogLevel.WARNING))
                return
            possible = min(possible, available // qty)

        if possible == 0:
            print(log("Not enough materials for processing.", LogLevel.WARNING))
            return

        # amount validation
        if amount is None:
            amount = 1
        if amount < 1:
            print(log("Amount must be at least 1.", LogLevel.WARNING))
            return
        if amount > possible:
            print(log(f"Cannot process {amount}x {recipe.ID}. Only {possible} possible due to limited materials.", LogLevel.WARNING))
            return

        # check for space in inventory for outputs
        for out_item, out_qty in recipe.outputs:
            space_available = player.inventory.spaceFor(out_item)
            required = out_qty * amount
            print(f"Checking output {out_item.name}: needs {required} slots, has {space_available} available.")
            if space_available < required:
                print(log(f"Not enough inventory space for output {out_item.name}.", LogLevel.WARNING))
                return

        # **Critical**: safe state of inventory (deepcopy of slots)
        backup_slots = copy.deepcopy(player.inventory.slots)

        # remove inputs
        for item, qty in recipe.inputs:
            if not player.inventory.removeItem(item, qty * amount):
                print(log(f"Failed to remove {qty * amount}x {item.name} from inventory. Rolling back.", LogLevel.WARNING))
                # restore from backup: rollback
                player.inventory.slots = backup_slots
                return

        # processing time
        totalTime = 0 if player.name == "test" else recipe.time * amount
        print(f"Processing {amount}x {recipe.ID}... Estimated time: ~{totalTime}s")
        time.sleep(totalTime)

        # 6. Outputs hinzufügen
        for out_item, out_qty in recipe.outputs:
            if not player.inventory.addItem(out_item, out_qty * amount):
                print(log(f"No room in inventory for the output {out_item.name}! Rolling back inputs.", LogLevel.WARNING))
                # restore from backup: rollback
                player.inventory.slots = backup_slots
                return

        print(f"Successfully processed {amount}x recipe '{recipe.ID}'!")

class Upgrader:
    def upgrade(self, player: Player):
        if player.pickaxe.mingLevel == 0:
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
        pass

# -----------------------------
# Helper functions
# -----------------------------

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

#dynamic way to print all the commands with accurate spacing to the longest command
commands = [
    ("mine", [(f"<material> <amount {{1..{Inventory.stack * 4}}}>?1", "Mine a material of additional count (e.g. '... coal 5')")]),
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

def printHelp():
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
    cmds = [(cmd[0], [(arg[0] if arg[0] else "None", arg[1]) for arg in cmd[1]]) for cmd in commands]

    maxCmdLength = max(len(cmd[0]) for cmd in cmds)
    maxArgLength = max(len(arg[0]) for cmd in cmds for arg in cmd[1])
    maxDescLength = 50  # Max length for description

    print(log("'?' means optional value with default value e.g. 4", LogLevel.TIP))
    print(log("'|' means or / option", LogLevel.TIP))

    print("\n╭" + "─" * (maxCmdLength + 2) + "┬" + "─" * (maxArgLength + 2) + "┬" + "─" * (maxDescLength + 2) + "╮")
    print(f"│ {'Command':<{maxCmdLength}} │ {'Arguments':<{maxArgLength}} │ {'Description':<{maxDescLength}} │")
    print("├" + "─" * (maxCmdLength + 2) + "┼" + "─" * (maxArgLength + 2) + "┼" + "─" * (maxDescLength + 2) + "┤")

    for cmd in commands:
        cmdName = cmd[0]
        args = cmd[1]
        for i, arg in enumerate(args):
            argText = arg[0] or "None"
            descText = arg[1]
            descWrapped = wordWrap(descText, maxDescLength)
            for j, line in enumerate(descWrapped):
                # Only print command name for the first argument/description
                if i == 0 and j == 0:
                    print(f"│ {cmdName:<{maxCmdLength}} │ {argText:<{maxArgLength}} │ {line:<{maxDescLength}} │")
                elif j == 0:
                    print(f"│ {'':<{maxCmdLength}} │ {argText:<{maxArgLength}} │ {line:<{maxDescLength}} │")
                else:
                    print(f"│ {'':<{maxCmdLength}} │ {'':<{maxArgLength}} │ {line:<{maxDescLength}} │")
            # After first argument, don't print command name again
            if i < len(args) - 1:
                print(f"│ {'':<{maxCmdLength}} ├{'─' * (maxArgLength + 2)}┼{'─' * (maxDescLength + 2)}┤")
            cmdName = ""
        # Print a separator line after each command's arguments/descriptions,
        # but only if this is not the last command in the list
        if cmd != commands[-1]:
            print("├" + "─" * (maxCmdLength + 2) + "┼" + "─" * (maxArgLength + 2) + "┼" + "─" * (maxDescLength + 2) + "┤")
    print("╰" + "─" * (maxCmdLength + 2) + "┴" + "─" * (maxArgLength + 2) + "┴" + "─" * (maxDescLength + 2) + "╯\n")

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
    print(f"│ {colorText('Recipe', '#A6C1EE')}  │ {recipe.ID:<45} │")
    print("├─────────┼────────────────────────────────────┬──────────┤")
    for item, qty in recipe.inputs:
        if item == recipe.inputs[0][0]: # makes 'Inputs' in first column only show the first input
            print(f"│ {colorText('Inputs', '#A6C1EE')}  │ {item.name:<34} │ {qty:>7}x │")
        else:
            print(f"│         │ {item.name:<34} │ {qty:>7}x │")
    print("├─────────┼────────────────────────────────────┼──────────┤")
    for item, qty in recipe.outputs:
        if item == recipe.outputs[0][0]: # makes 'Outputs' in first column only show the first output
            print(f"│ {colorText('Outputs', '#A6C1EE')} │ {item.name:<34} │ {qty:>7}x │")
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

def hexToRGB(hexColor: str) -> tuple[int, int, int]:
    hexColor = hexColor.lstrip('#')
    return tuple(int(hexColor[i:i + 2], 16) for i in (0, 2, 4))

def interpolateMultiColor(colors: list[tuple[int, int, int]], factor: float) -> tuple[int, int, int]:
    if factor <= 0:
        return colors[0]
    if factor >= 1: 
        return colors[-1]

    totalSegments = len(colors) - 1
    scaled = factor * totalSegments
    index = int(scaled)
    innerFac = scaled - index

    color_start = colors[index]
    color_end = colors[index + 1]

    return tuple(
        int(cs + (ce - cs) * innerFac)
        for cs, ce in zip(color_start, color_end)
    )

def gradientText(text: str, hexColors: tuple[str], direction: str = "lr") -> str:
    if len(hexColors) < 2:
        raise ValueError("At least two colors are required.")

    rgbColors = [hexToRGB(h) for h in hexColors]
    lines = text.splitlines()

    def applyGradient(items: list[str], reverse: bool = False) -> list[str]:
        if reverse:
            items = items[::-1]
        total = len(items) - 1 if len(items) > 1 else 1
        result = []
        for i, item in enumerate(items):
            factor = i / total
            rgb = interpolateMultiColor(rgbColors, factor)
            result.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{item}")
        if reverse:
            result = result[::-1]
        return result

    if direction in ("td", "bu"):
        reverse = direction == "bu"
        linesProc = lines[::-1] if reverse else lines
        coloredLines = applyGradient(linesProc, reverse=False)
        if reverse:
            coloredLines = coloredLines[::-1]
        # Jede Zeile am Ende resetten
        return "\n".join(line + "\033[0m" for line in coloredLines)

    elif direction in ("lr", "rl"):
        reverse = direction == "rl"
        result = []
        for line in lines:
            chars = list(line)
            coloredChars = applyGradient(chars, reverse)
            result.append("".join(coloredChars) + "\033[0m")
        return "\n".join(result)

    else:
        raise ValueError("Direction must be one of: 'lr', 'rl', 'td', 'bu'")

def colorText(text: str, hexColor: str) -> str:
    rgb = hexToRGB(hexColor)
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"

# Unreadable text
def obfuscateText(text: str) -> str:
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(charset) if c != ' ' else ' ' for c in text)

# print(gradientText("Zars\nhallo\nP14a", ("#FBC2EB", "#A6C1EE"), "bu")) # !testing
# print(colorText("Zars\nhallo\nP14a", "#FBC2EB")) # !testing

def getUnlockedCommands():
    return {
        # takes all ressources available
        'mine': { block.ID: None for block in Block.all() },
        'inventory': None,
        'recipe': {
            'search': None,
            'get': { recipe.ID: None for recipe in Recipe.all() },
            'show': { recipe.ID: None for recipe in Recipe.all() }
        },
        'status': None,
        'process': { recipe.ID: None for recipe in Recipe.all() },
        'help': None,
        'exit': None,
    }

# -----------------------------
# Main Game Loop
# -----------------------------
def main():
    installPackages()

    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.completion import NestedCompleter

    print(gradientText(asciiArtLogo, ("#FBC2EB", "#A6C1EE"), "lr"))
    name = input("\nWhat's your name again? # ")
    player = Player(name)
    processor = Processor()
    #upgrader = Upgrader()
    #bizman = Bizman()

    print(gradientText(asciiArtPlanet, ("#E4BDD4", "#4839A1"), "td"))
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

Type '{colorText("help", '#A7E06F')}' to see all available commands.

⌇ Good luck, {colorText(player.name, "#FBC2EB")}.
⌇ - And remember: Humanity counts on you!
""")
    def handleExit():
        print(f"\nMemory encrypted!\nPlanet {gradientText('Zars P14a', ('#FBC2EB', '#A6C1EE'))} is waiting for you to return.\n\nData(Player('{player.name}')): [\n\t{obfuscateText('ashdih askdhaiwuihh asiudhwudbn asdhkjhwih aksjdhdwi')}\n]\n")

    command_completer = NestedCompleter.from_nested_dict(getUnlockedCommands())

    history = InMemoryHistory()
    session = PromptSession(history=history, completer=command_completer)

    while True:
        try:
            command = session.prompt("What do you want to do, pioneer? # ").strip().lower()

            parts = command.split()

            if command == "exit":
                handleExit()
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
                print(player.inventory)
            elif command == "status":
                print(f"\nName: {player.name}")
                print(f"Tool: {player.tool.name} (Level {player.tool.miningLevel})")
                print("Inventory:", player.inventory, "\n")
            elif command.startswith("process"):
                if len(parts) >= 2:
                    recipe = Recipe.get(parts[1])
                    anzahl = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                    processor.process(player, recipe, anzahl)
                else:
                    print(log("Pioneer! Provide a recipe name, e.g. 'process iron' or with a count 'process iron 5'.", LogLevel.WARNING))
            #elif command == "upgrade":
            #    anton.upgradeTool(player)
            #elif command == "antiquity":
            #    vincent.createAntiquity(player)
            elif command.startswith("recipe"):
                if len(parts) >= 3 and parts[1] == "search":
                    searchTerm = " ".join(parts[2:])
                    allIDs = list(Recipe.Registry.keys())
                    # Fuzzy search mit difflib
                    matches = difflib.get_close_matches(searchTerm, allIDs, n=10, cutoff=0.3)
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

        except KeyboardInterrupt:
            handleExit()
            break

# Start the game
main()
