import difflib
import time
import random
import string
import copy
import re
from typing import Union
from enum import Enum
from registry import Item, Tool, Block, Recipe, DropRateEnum

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion, NestedCompleter

class LogLevel(Enum):
    ERROR = {"color": "#FF6961", "symbol": "⊘"}
    WARNING = {"color": "#FFB561", "symbol": "⊜"}
    TIP = {"color": "#6A7EAC", "symbol": "⊙"}
    SUCCESS = {"color": "#A7E06F", "symbol": "⊛"}

def log(message: str, level: LogLevel) -> str:
    color = level.value["color"]
    symbol = level.value["symbol"]
    return f"{colorText(symbol + " " + message, color)}"

def stripColor(text: str) -> str:
    # Remove ANSI escape sequences for colors
    ansi_pattern = re.compile(r'\033\[[0-9;]*m')
    return ansi_pattern.sub('', text)

class Inventory:
    stack: int = 64

    def __init__(self, owner = None):
        self.owner = owner
        # Every slot is a Dictionary with "item" and "count"
        self.slots = []
        self.maxSlots: int = 32

    def addItem(self, item: Item, quantity: int = 1):
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
                print(log(f"No free space inventory space for {item.name}!", LogLevel.WARNING))
                return False
        return True

    def removeItem(self, item: Item, quantity: int = 1):
        removed: int = 0
        for slot in self.slots:
            if slot["item"] == item:
                canRemove = min(slot["count"], quantity - removed)
                slot["count"] -= canRemove
                removed += canRemove
        # Remove empty slots
        self.slots = [slot for slot in self.slots if slot["count"] > 0]
        if removed < quantity:
            print(log(f"Not enough {item.name} to remove!", LogLevel.WARNING))
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
        sortedSlots = sorted(self.slots, key=lambda slot: slot["item"].name.lower())
        slotCount = len(sortedSlots)

        # Always show 1 column minimum
        if slotCount <= 8:
            columns = 1
        elif slotCount <= 26:
            columns = 2
        else:
            columns = 3

        cWidth = 21  # column width
        aWidth = 6   # amount width
        ftWidth = 13 # footer titles width

        # Table symbols
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

        # Row formatting functions
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

        # Even when empty, show one empty row
        if slotCount == 0:
            rows = [cRow([])]
        else:
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

        # Footer
        tWidth = (cWidth + aWidth + 6) * columns + 1

        if columns == 1:
            output += f"{sl}{lh * ftWidth}{st}{lh * (cWidth + 2 - (ftWidth + 1))}{sb}{lh * (aWidth + 2)}{sr}\n"
        elif columns == 2:
            output += f"{sl}{lh * ftWidth}{st}{lh * (cWidth + 2 - (ftWidth + 1))}{sb}{lh * (aWidth + 2)}{sb}{lh * (cWidth + 2)}{sb}{lh * (aWidth + 2)}{sr}\n"
        else:
            output += f"{sl}{lh * ftWidth}{st}{lh * (cWidth + 2 - (ftWidth + 1))}{sb}{lh * (aWidth + 2)}{sb}"
            for _ in range(columns - 2):
                output += f"{lh * (cWidth + 2)}{sb}{lh * (aWidth + 2)}{sb}"
            output += f"{lh * (cWidth + 2)}{sb}{lh * (aWidth + 2)}{sr}\n"

        output += f"{lv} Total Items │ {(str(self.totalItems()) + '/' + str(self.stack * self.maxSlots)):>{tWidth - 18}} {lv}\n"
        output += f"{lv} Stacks      │ {(str(len(self.slots)) + '/' + str(self.maxSlots)):>{tWidth - 18}} {lv}\n"
        money_str = self.owner.displayMoney() if self.owner else "N/A"
        output += f"{lv} Money       │ {money_str:>{tWidth - 19}} {lv}\n"
        output += f"{cbl}{lh * ftWidth}{sb}{lh * (tWidth - 16)}{cbr}\n"

        return output

class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = Inventory(owner=self)
        self.tool = Tool.get("wooden_pickaxe")  # Start with a wooden pickaxe
        self.money = 0

        if name == "testable":  # Special test player
            self.tool = Tool.get("test_tool")  # Start with a test tool

    def mine(self, material: str, amount: int = 1):
        block = Block.get(material)

        if not block or not Block.exists(material):
            print(log(f"Unable to mine '{material}' because it's not scannable!", LogLevel.WARNING))
            return

        # Check if the mining level of the tool is sufficient
        if self.tool.miningLevel < block.miningLevel and self.tool.miningLevel != -1:
            print(log(f"Tool too weak to mine {block.ID}!", LogLevel.WARNING))
            return
        
        if amount > self.inventory.stack * 4:
            log("Why so much?", LogLevel.WARNING)

        total = 0
        for _ in range(amount):
            drops = block.dropRates
            _min = drops.getRateFor(DropRateEnum.MIN)
            _max = drops.getRateFor(DropRateEnum.MAX)

            # Drop amount based on drop rates calculation
            while _min < _max:
                if random.random() <= drops.getRateFor(DropRateEnum.RATE):
                    _min += 1
                else:
                    break
            total += _min

        # Testing available space in inventory
        possible = (self.inventory.maxSlots * self.inventory.stack) - self.inventory.totalItems()
        if possible <= total:
            print(log("Inventory is full!", LogLevel.WARNING))
            return

        # Mining time calculation
        totalTime = 0 if self.tool.miningLevel == -1 else block.miningTime * amount / self.tool.timeFac
        print(f"\nTool: {self.tool.name}\nMining: {block.ID} ({amount}x)\nTime: ~{totalTime:.2f}s\n")

        # Simulate mining time
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
    def process(self, player: Player, recipe: Recipe, amount: Union[int, str] = 1):
        if not recipe:
            print(log(f"No recipe found for {recipe}.", LogLevel.WARNING))
            return

        possible = float('inf')
        for i, n in recipe.inputs:
            available = player.inventory.totalItemsOf(i)
            possible = min(possible, available // n)

        if amount == "all":
            amount = possible

        if amount is None:
            amount = 1
        if amount < 1:
            print(log("Amount must be at least 1.", LogLevel.WARNING))
            return

        possible = float('inf')
        print("\n╭────────────────────────────────────────┬─────────╮")
        colored = colorText(str(recipe.ID), '#A6C1EE')
        plain = stripColor(colored)
        padding = 38 + (len(colored) - len(plain))
        print(f"│ {colored:<{padding}} │ {str(amount):>6}x │")
        print("├───────────────────────┬────────────────┼─────────┤")
        print("│ Needed Items          │ Available      │ Missing │")
        print("├───────────────────────┼────────────────┼─────────┤")
        for item, n in recipe.inputs:
            required = n * amount
            available = player.inventory.totalItemsOf(item)
            possible = min(possible, available // n)
            missing = max(0, required - available)
            print(f"│ {item.name:<21} │ {(str(available) + '/' + str(required)):<14} │ {missing:>6}x │")
        print("├──────────┬────────────┴────────────────┴─────────┤")
        print(f"│ Possible │ {possible:>36}x │")
        print("╰──────────┴───────────────────────────────────────╯\n")

        if possible == 0:
            print(log("Not enough materials for processing.\n", LogLevel.WARNING))
            return
        
        if amount > possible:
            print(log(f"Cannot process {amount}x {recipe.ID}. Only {possible} possible due to limited materials.\n", LogLevel.WARNING))
            return

        # **Critical**: Safe state of inventory (deepcopy of slots)
        backupSlots = copy.deepcopy(player.inventory.slots)

        # Remove inputs
        for i, n in recipe.inputs:
            if not player.inventory.removeItem(i, n * amount):
                print(log(f"Failed to remove {n * amount}x {i.name} from inventory. Rolling back.", LogLevel.WARNING))
                # restore from backup: rollback
                player.inventory.slots = backupSlots
                return

        # Processing time
        totalTime = 0 if player.tool.miningLevel == -1 else recipe.time * amount
        print(f"Processing {amount}x {recipe.ID}... Estimated time: ~{totalTime:.2f}s")
        time.sleep(totalTime)

        # Add outputs to inventory
        for i, n in recipe.outputs:
            if not player.inventory.addItem(i, n * amount):
                print(log(f"No room in inventory for the output {i.name}! Rolling back inputs.", LogLevel.WARNING))
                # Restore from backup: rollback
                player.inventory.slots = backupSlots
                return

        print(log(f"Successfully processed {amount}x recipe '{recipe.ID}'!\n", LogLevel.SUCCESS))

class Shop:
    def upgrade(self, player: Player, tool: str):
        if not tool or not isinstance(tool, str):
            print(log(f"Invalid tool name: {tool}.", LogLevel.WARNING))
            return

        newTool = Tool.get(tool)
        if not newTool:
            print(log(f"No tool found for '{tool}'.", LogLevel.WARNING))
            return

        if newTool.miningLevel <= player.tool.miningLevel:
            print(log(f"Your {player.tool.name} is already at or above the level of {newTool.name}.", LogLevel.WARNING))
            return

        print("\n╭────────────────────────────────────────┬─────────╮")
        colored = colorText(str(newTool.name), '#A6C1EE')
        plain = stripColor(colored)
        padding = 38 + (len(colored) - len(plain))
        print(f"│ {colored:<{padding}} │ Upgrade │")
        print("├───────────────────────┬────────────────┼─────────┤")
        print("│ Needed Items          │ Available      │ Missing │")
        print("├───────────────────────┼────────────────┼─────────┤")
        
        allAvailable = True  # Flag for checking if all required items are available
        for item, required in newTool.costs:
            available = player.inventory.totalItemsOf(item)
            missing = max(0, required - available)
            print(f"│ {item.name:<21} │ {(str(available) + '/' + str(required)):<14} │ {missing:>6}x │")
            if missing > 0:
                allAvailable = False
        
        print("╰───────────────────────┴────────────────┴─────────╯\n")

        if not allAvailable:
            print(log("Upgrading canceled due to insufficient upgrade ressource supply.", LogLevel.WARNING))
            return

        # **Critical**: Safe state of inventory (deepcopy of slots)
        backupSlots = copy.deepcopy(player.inventory.slots)

        # Remove materials from inventory
        for item, quantity in newTool.costs:
            if not player.inventory.removeItem(item, quantity):
                print(log(f"Failed to remove {quantity}x {item.name}. Rolling back.", LogLevel.WARNING))
                player.inventory.slots = backupSlots
                print(log("Inventory restored from backup.", LogLevel.TIP))
                return
            print(log(f"Removed {quantity}x {item.name}.", LogLevel.TIP))

        # Processing upgrade
        player.tool = newTool
        print(log(f"Successfully upgraded to {newTool.name}!", LogLevel.SUCCESS))

# -----------------------------
# Helper functions
# -----------------------------

# Word wrapping function to split text into lines of max. n characters
def wordWrap(text: str, n: int = 50) -> list[str]:
    words = text.split()
    lines = []
    current = ""

    for word in words:
        # Check if adding the word exceeds the limit
        if len(current) + len(word) + (1 if current else 0) > n:
            lines.append(current)
            current = word
        else:
            current += (" " if current else "") + word
    if current:
        lines.append(current)
    return lines

# Dynamic way to print all the commands with accurate spacing to the longest command
commands = [
    ("mine", [(f"<material> [<amount {{1..{Inventory.stack * 4}}}>?1|all]", "Mine a material of additional count (e.g. '... coal 5')")]),
    ("inventory", [(None, "Show your current inventory")]),
    ("status", [(None, "Show your status (name, tool, inventory)")]),
    ("process", [("<recipe> <amount>?1", "Process material according to the recipe (e.g. '... iron_ingot 2')")]),
    ("recipe", [("<name>", "Get a recipe by name")]),
    ("upgrade", [("<tool>", "Upgrade tool to higher grade")]),
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

    print()
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

# Convert hex color to RGB tuple
def hexToRGB(hexColor: str) -> tuple[int, int, int]:
    hexColor = hexColor.lstrip('#')
    return tuple(int(hexColor[i:i + 2], 16) for i in (0, 2, 4))

# Interpolate multiple colors based on a factor (0.0 to 1.0)
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

# Gradient text function
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

# Color text function
def colorText(text: str, hexColor: str) -> str:
    rgb = hexToRGB(hexColor)
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"

# Unreadable text
def obfuscateText(text: str) -> str:
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(charset) if c != ' ' else ' ' for c in text)

# -----------------------------
# Main Game Loop
# -----------------------------
def main():
    print(gradientText(asciiArtLogo, ("#FBC2EB", "#A6C1EE"), "lr"))
    name = input("\nWhat's your name again? # ")
    player = Player(name)
    processor = Processor()
    shop = Shop()

    print(gradientText(asciiArtPlanet, ("#E4BDD4", "#4839A1"), "td"))

    # Welcome message with "story" (ironically)
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

    # Function to handle exit
    def handleExit():
        print(f"\nMemory encrypted!\nPlanet {gradientText('Zars P14a', ('#FBC2EB', '#A6C1EE'))} is waiting for you to return.\n\nData(Player('{player.name}')): [\n\t{obfuscateText('ashdih askdhaiwuihh asiudhwudbn asdhkjhwih aksjdhdwi')}\n]\n")

    # --------------------------------------
    # Command completer using prompt_toolkit
    # --------------------------------------
    class FuzzyCompleter(Completer):
        def __init__(self, completionsDict):
            self.completions_dict = {
                tuple(k.split()): v for k, v in completionsDict.items()
            }

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor.lower()
            parts = text.split()

            # Find matching command paths
            for cmd_path, completions in self.completions_dict.items():
                # Check if the input starts with the command path
                if len(parts) >= len(cmd_path) and parts[:len(cmd_path)] == list(cmd_path):
                    search_term = parts[len(cmd_path)] if len(parts) > len(cmd_path) else ''
                    # Find completions containing the search term
                    matches = [
                        item for item in completions
                        if search_term.lower() in item.lower()
                    ]
                    # Sort by similarity
                    matches = difflib.get_close_matches(search_term, matches, n=10, cutoff=0.0)
                    for match in matches:
                        yield Completion(
                            match,
                            start_position=-len(search_term) if search_term else 0,
                            display=match
                        )

    def getUnlockedCommands(player: Player):
        currentTool = player.tool
        currentLevel = currentTool.miningLevel if currentTool else 0

        return {
            'mine': { block.ID: None for block in Block.all() },
            'inventory': None,
            'recipe': None,
            'status': None,
            'upgrade': {
                tool.ID: None
                for tool in Tool.all()
                if tool.miningLevel >= currentLevel and tool != currentTool and tool.ID not in ["test_tool"]
            },
            'process': { recipe.ID: None for recipe in Recipe.all() },
            'help': None,
            'exit': None
        }

    def createCompleter(player):
        baseCommands = getUnlockedCommands(player)
        # Initialize fuzzy completer with completion lists for specific commands
        fuzzyCompletions = {
            'recipe': { recipe.ID: None for recipe in Recipe.all() }
            # Add more command paths as needed, e.g., 'mine': list(Block.Registry.keys())
        }
        fuzzyCompleter = FuzzyCompleter(fuzzyCompletions)
        nestedCompleter = NestedCompleter.from_nested_dict(baseCommands)

        class CombinedCompleter(Completer):
            def get_completions(self, document, complete_event):
                text = document.text_before_cursor.lower()
                # Use fuzzy completer for registered command paths
                for cmd_path in fuzzyCompletions:
                    if text.startswith(cmd_path):
                        yield from fuzzyCompleter.get_completions(document, complete_event)
                        return
                # Fallback to nested completer for other commands
                yield from nestedCompleter.get_completions(document, complete_event)
            
        return CombinedCompleter()

    # Initialize prompt session with history and completer
    history = InMemoryHistory()
    commandCompleter = createCompleter(player)
    session = PromptSession(
        history=history,
        completer=commandCompleter
    )

    # Main game loop with commands
    while True:
        attempts = 0
        try:
            # Random speech lines for the player
            speechLines = [
                "What do you want to do?",
                "What's your next step, pioneer?",
                "How can I assist you?",
                "Ready for the next task?",
                "What is your command, pioneer?",
                "The frontier awaits your decision.",
                "Command received... awaiting further orders.",
                "What's our next move, trailblazer?",
                "All systems ready. What's your plan?",
                "Another day, another mission. What's first?",
                "Standing by for your instructions.",
                "What's the next challenge?",
                "Your journey continues. What's next?",
                "The unknown calls. How do we proceed?",
                "You lead the way! What now?",
                "The universe is vast, and so are your choices.",
            ]

            command = session.prompt(f"{"What are you waiting for? Orders, Pioneer!" if attempts == 0 else random.choice(speechLines)} # ").strip()

            parts = command.split()

            if command == "exit":
                handleExit()
                break
            elif command == "help":
                printHelp()
            elif command.startswith("mine"):
                if len(parts) in range(2, 4): # 2-3 parts
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
                if len(parts) in range(2, 4):
                    recipe = Recipe.get(parts[1])
                    amount = 1

                    if len(parts) == 3:
                        if parts[2] == "all":
                            amount = "all"
                        elif parts[2].isdigit():
                            amount = int(parts[2])
                        elif not parts[2]:
                            amount = 1
                        else:
                            print(log(f"Invalid amount: '{parts[2]}'. Use a number or 'all'.", LogLevel.WARNING))
                            continue

                    if recipe:
                        processor.process(player, recipe, amount)
                    else:
                        print(log(f"No recipe found with name '{parts[1]}'.", LogLevel.WARNING))
                else:
                    print(log("Usage: process <recipe> [amount|all]?1", LogLevel.WARNING))
            elif command.startswith("upgrade"):
                if len(parts) != 2:
                    print(log("Usage: upgrade <tool-id>", LogLevel.WARNING))
                    continue
                shop.upgrade(player, parts[1])
            elif command.startswith("recipe"):
                if len(parts) == 2:
                    recipeName = parts[2]
                    recipe = Recipe.get(recipeName)
                    if recipe:
                        printRecipe(recipe)
                    else:
                        print(log(f"No recipe found with name '{recipeName}'.", LogLevel.WARNING))
                else:
                    print(log("Usage: recipe <name>", LogLevel.WARNING))
            else:
                print(log("Pioneer! We don't know this one. Type 'help' for an overview!", LogLevel.ERROR))

        # Handle exceptions where Ctrl+C is pressed
        except KeyboardInterrupt:
            handleExit()
            break

# Start the game
main()
