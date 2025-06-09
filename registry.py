from collections import namedtuple
from enum import Enum

class Item:
    Registry = {}

    def __init__(self, ID: str, name: str):
        self.ID = ID
        self.name = name

    def __repr__(self):
        return f"<Item: {self.name}>"

    def __eq__(self, other):
        return isinstance(other, Item) and self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    @classmethod
    def register(cls, ID: str, name: str):
        item = cls(ID, name)
        cls.Registry[ID] = item
        setattr(cls, ID.upper(), item)
        return item

    @classmethod
    def get(cls, ID: str):
        return cls.Registry.get(ID)

    @classmethod
    def all(cls):
        return list(cls.Registry.values())

class Tool:
    Registry = {}

    def __init__(self, ID: str, name: str, miningLevel: int, timeFac: float):
        self.ID = ID
        self.name = name
        self.miningLevel = miningLevel
        self.timeFac = timeFac

        if not isinstance(ID, str):
            raise TypeError(f"Tool ID must be a string: {ID}")
        if not isinstance(name, str):
            raise TypeError(f"Tool name must be a string: {name}")
        if not isinstance(miningLevel, int):
            raise TypeError(f"Mining level must be an integer: {miningLevel}")
        if not isinstance(timeFac, float):
            raise TypeError(f"Mining time must be a number of type float: {timeFac}")

    def __repr__(self):
        return f"<Tool: {self.name} (Lvl {self.miningLevel})>"

    def __eq__(self, other):
        return isinstance(other, Tool) and self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    @classmethod
    def register(cls, ID: str, name: str, miningLevel: int, timeFac: float):
        tool = cls(ID, name, miningLevel, timeFac)
        cls.Registry[ID] = tool
        setattr(cls, ID.upper(), tool)
        return tool

    @classmethod
    def get(cls, ID: str):
        return cls.Registry.get(ID)

    @classmethod
    def all(cls):
        return list(cls.Registry.values())

DropRateEnum = Enum('DropRate', 'MIN MAX RATE')

class DropRates:
    def __init__(self, _min: int, _max: int, rate: float):
        if _min < 0 or _max < 0 or rate < 0:
            raise ValueError("DropRates values must be non-negative")
        if _min > _max:
            raise ValueError("Minimum drop cannot be greater than maximum drop")

        self._min = _min
        self._max = _max
        self.rate = rate

    def __repr__(self):
        return f"<DropRates {self._min}-{self._max} at rate of {self.rate}>"

    def __copy__(self):
        return DropRates(self._min, self._max, self.rate)
    
    def getRateFor(self, dropRate: DropRateEnum):
        if dropRate == DropRateEnum.MIN:
            return self._min
        elif dropRate == DropRateEnum.MAX:
            return self._max
        elif dropRate == DropRateEnum.RATE:
            return self.rate
        else:
            raise ValueError(f"Invalid DropRateEnum value: {dropRate}")

class Block:
    Registry = {}

    def __init__(self, ID: str, dropItem: Item, miningLevel: int, miningTime: float, dropRates: DropRates):
        self.ID = ID
        self.name = dropItem.name
        self.dropItem = dropItem
        self.miningLevel = miningLevel
        self.miningTime = miningTime
        self.dropRates = dropRates

    def __repr__(self):
        return f"<Block: {self.ID} drops {self.dropItem.name} with min. mining level {self.miningLevel} and relative time {self.miningTime} seconds>"

    def __eq__(self, other):
        return isinstance(other, Block) and self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    @classmethod
    def register(cls, ID: str, dropItem: Item, miningLevel: int, miningTime: float, dropRates: DropRates):
        block = cls(ID, dropItem, miningLevel, miningTime, dropRates)
        cls.Registry[ID] = block
        setattr(cls, ID.upper(), block)
        return block

    @classmethod
    def get(cls, ID: str):
        return cls.Registry.get(ID)

    @classmethod
    def all(cls):
        return list(cls.Registry.values())
    
    @classmethod
    def getDrop(cls, item: Item, dropRates: DropRateEnum):
        for block in cls.Registry.values():
            if block.dropItem == item:
                return block
        return None

RecipeType = namedtuple("RecipeType", ["id", "inputs", "outputs"])

class Recipe:
    Registry = {}

    def __init__(self, ID: str, inputs, outputs): # inputs and outputs are lists of tuples (Item, quantity) or just one tuple
        self.ID = ID
        self.inputs = inputs
        self.outputs = outputs

        if not isinstance(inputs, (list, tuple)):
            raise ValueError(f"Recipe '{ID}' must have at least one input.")
        if type(inputs) is list and not all(isinstance(i, tuple) for i in inputs):
            raise TypeError(f"All inputs in list for recipe '{ID}' must be tuples.")
        if not all(isinstance(i[0], Item) and isinstance(i[1], int) for i in inputs):
            raise TypeError(f"All inputs for recipe '{ID}' must be (Item, quantity) tuples.")
        if not isinstance(outputs, (list, tuple)):
            raise ValueError(f"Recipe '{ID}' must have at least one output.")
        if type(outputs) is list and not all(isinstance(i, tuple) for i in outputs):
            raise TypeError(f"All outputs in list for recipe '{ID}' must be tuples.")
        if not all(isinstance(i[0], Item) and isinstance(i[1], int) for i in outputs):
            raise TypeError(f"All outputs for recipe '{ID}' must be (Item, quantity) tuples.")
        
    def __repr__(self):
        return f"<Block {self.ID} takes {self.inputs} to make {self.outputs}>"

    @classmethod
    def register(cls, ID, inputs, outputs):
        recipe = cls(ID, inputs, outputs)
        cls.Registry[ID] = recipe
        setattr(cls, ID.upper(), recipe)

    @classmethod
    def get(cls, ID):
        return cls.Registry.get(ID)

#Item.register("<id>", "<name>")

Item.register("cobbled_stone", "Cobbled Stone")

Item.register("coal", "Coal")
Item.register("raw_iron", "Raw Iron")
Item.register("raw_copper", "Raw Copper")
Item.register("raw_gold", "Raw Gold")
Item.register("raw_aluminium", "Raw Aluminium")
Item.register("raw_veridium", "Raw Veridium")
Item.register("raw_titanium", "Raw Titanium")
Item.register("raw_zarsium", "Raw Zarsium")

Item.register("copper_ingot", "Copper Ingot")
Item.register("iron_ingot", "Iron Ingot")
Item.register("gold_ingot", "Gold Ingot")
Item.register("aluminium_ingot", "Aluminium Ingot")
Item.register("veridium_ingot", "Veridium Ingot")
Item.register("titanium_ingot", "Titanium Ingot")
Item.register("zarsium_ingot", "Zarsium Ingot")

Item.register("steel_ingot", "Steel Ingot")

#Tool.register("<id>", "<name>", <mining-lvl>, <time-divisor (2.0=200% fast)>)

Tool.register("wood_pickaxe", "Wooden Pickaxe", 0, 0.5)
Tool.register("iron_pickaxe", "Iron Pickaxe", 1, 1.0)

Tool.register("test_tool", "Test Tool", 9999, 9999.0)

#Block.register("<name>", Item.<id>, <mining-lvl>, <time-sec>, DropRates(<min>, <max>, <rate (1=100%)>))

Block.register("coal", Item.COAL, 0, 2, DropRates(1, 3, 0.2))
Block.register("iron", Item.RAW_IRON, 1, 3, DropRates(1, 2, 0.07))
Block.register("copper", Item.RAW_COPPER, 1, 2.5, DropRates(1, 2, 0.07))
Block.register("gold", Item.RAW_GOLD, 2, 3.5, DropRates(1, 2, 0.07))
Block.register("aluminium", Item.RAW_ALUMINIUM, 2, 3.5, DropRates(1, 2, 0.07))
Block.register("veridium", Item.RAW_VERIDIUM, 3, 4, DropRates(1, 2, 0.07))
Block.register("titanium", Item.RAW_TITANIUM, 4, 4.5, DropRates(1, 2, 0.07))
Block.register("stone", Item.COBBLED_STONE, 0, 1.5, DropRates(1, 1, 1.0))

#Recipe.register(
#   "<name>",
#   [...(Item.<id>, <amount>)],
#   [...(Item.<id>, <amount>)],
#)

Recipe.register(
    "iron_ingot",
    [(Item.RAW_IRON, 1)],
    [(Item.IRON_INGOT, 1)]
)
Recipe.register(
    "copper_ingot",
    [(Item.RAW_COPPER, 1)],
    [(Item.COPPER_INGOT, 1)]
)
Recipe.register(
    "steel_ingot",
    [(Item.IRON_INGOT, 2), (Item.COAL, 1)],
    [(Item.STEEL_INGOT, 1)]
)