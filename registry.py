from enum import Enum
from typing import Union

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

    def __init__(self, ID: str, name: str):
        self.ID = ID
        self.name = name
        self.miningLevel = 0
        self.timeFac = 1.0

        if not isinstance(ID, str):
            raise TypeError(f"Tool ID must be a string: {ID}")
        if not isinstance(name, str):
            raise TypeError(f"Tool name must be a string: {name}")

    def __repr__(self):
        return f"<Tool: {self.name} (Lvl {self.miningLevel})>"

    def __eq__(self, other):
        return isinstance(other, Tool) and self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    @classmethod
    def register(cls, ID: str, name: str):
        tool = cls(ID, name)
        cls.Registry[ID] = tool
        setattr(cls, ID.upper(), tool)
        return ToolBuilder(tool)

    @classmethod
    def get(cls, ID: str):
        return cls.Registry.get(ID)

    @classmethod
    def all(cls):
        return list(cls.Registry.values())

class ToolBuilder:
    def __init__(self, tool: Tool):
        self.tool = tool

    def costs(self, items: list[Union[Item, tuple[Item, int]]]):
        normalized = []
        for i in items:
            if isinstance(i, tuple):
                normalized.append(i)
            else:
                normalized.append((i, 1))
        self.recipe.inputs = normalized
        return self

    def level(self, miningLevel: int):
        self.tool.miningLevel = miningLevel
        return self

    def timeFac(self, timeFac: float):
        self.tool.timeFac = timeFac
        return self

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

    def __init__(self, ID: str):
        self.ID = ID
        self.dropItem = None
        self.miningLevel = 0
        self.miningTime = 1.0
        self.dropRates = DropRates(1, 1, 1.0)

    def __repr__(self):
        return f"<Block: {self.ID} drops {self.dropItem.name} with min. mining level {self.miningLevel} and relative time {self.miningTime} seconds>"

    def __eq__(self, other):
        return isinstance(other, Block) and self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    @classmethod
    def register(cls, ID: str):
        block = cls(ID)
        cls.Registry[ID] = block
        setattr(cls, ID.upper(), block)
        return BlockBuilder(block)

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

    @classmethod
    def exists(cls, ID: str) -> bool:
        return ID in cls.Registry

class BlockBuilder:
    def __init__(self, block: Block):
        self.block = block

    def drops(self, dropItem: Item):
        self.block.dropItem = dropItem
        return self

    def level(self, miningLevel: int):
        self.block.miningLevel = miningLevel
        return self

    def time(self, miningTime: float):
        self.block.miningTime = miningTime
        return self

    def rates(self, _min: int, _max: int, rate: float):
        self.block.dropRates = DropRates(_min, _max, rate)
        return self

class Recipe:
    Registry = {}

    def __init__(self, ID: str): # inputs and outputs are lists of tuples (Item, quantity) or just one tuple
        self.ID = ID
        self.inputs = []
        self.outputs = []
        self.time = 1.0 # in seconds
        
    def __repr__(self):
        return f"<Block {self.name} ({self.ID}) takes {self.inputs} to make {self.outputs}>"

    @classmethod
    def register(cls, ID: str):
        recipe = cls(ID)
        cls.Registry[ID] = recipe
        setattr(cls, ID.upper(), recipe)
        return RecipeBuilder(recipe)

    @classmethod
    def get(cls, ID):
        return cls.Registry.get(ID)
    
    @classmethod
    def all(cls):
        return list(cls.Registry.values())

class RecipeBuilder:
    def __init__(self, recipe: Recipe):
        self.recipe = recipe

    def inputs(self, inputs: list[Union[Item, tuple[Item, int]]]):
        normalized = []
        for inp in inputs:
            if isinstance(inp, tuple):
                normalized.append(inp)
            else:
                normalized.append((inp, 1))
        self.recipe.inputs = normalized
        return self

    def outputs(self, outputs: list[Union[Item, tuple[Item, int]]]):
        normalized = []
        for out in outputs:
            if isinstance(out, tuple):
                normalized.append(out)
            else:
                normalized.append((out, 1))
        self.recipe.outputs = normalized
        return self
    
    def time(self, time: float = 1.0):
        self.recipe.time = time
        return self

class ResearchPoint:
    Registry = {}
    Researched = []

    def __init__(self, ID: str, name: str):
        self.ID = ID
        self.name = name
        self.costsItems = []
        self.costsMoney = 0
        self.blocks = []
        self.tools = []
        self.recipes = []

    def __repr__(self):
        return f"<ResearchPoint: {self.name}>"

    def __eq__(self, other):
        return isinstance(other, ResearchPoint) and self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    @classmethod
    def register(cls, ID: str, name: str):
        rp = cls(ID, name)
        cls.Registry[ID] = rp
        setattr(cls, ID.upper(), rp)
        return ResearchBuilder(rp)  # << Here the builder is given back

    @classmethod
    def get(cls, ID: str):
        return cls.Registry.get(ID)

    @classmethod
    def all(cls):
        return list(cls.Registry.values())

    @classmethod
    def research(cls, ID: str):
        if ID not in cls.Researched:
            cls.Researched.append(ID)
            return True
        return False

    @classmethod
    def isResearched(cls, ID: str):
        return ID in cls.Researched


class ResearchBuilder:
    def __init__(self, researchPoint: ResearchPoint):
        self.researchPoint = researchPoint

    def costs(self, items: list[tuple[Item, int]] = [], money: int = 0):
        self.researchPoint.costsItems = items
        self.researchPoint.costsMoney = money
        return self

    def blocks(self, blocks: list[Block]):
        self.researchPoint.blocks.extend(blocks)
        return self

    def tools(self, tools: list[Tool]):
        self.researchPoint.tools.extend(tools)
        return self

    def recipes(self, recipes: list[Recipe]):
        self.researchPoint.recipes.extend(recipes)
        return self

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
Item.register("brass_ingot", "Brass Ingot")
Item.register("gold_ingot", "Gold Ingot")
Item.register("aluminium_ingot", "Aluminium Ingot")
Item.register("veridium_ingot", "Veridium Ingot")
Item.register("titanium_ingot", "Titanium Ingot")
Item.register("zarsium_ingot", "Zarsium Ingot")
Item.register("steel_ingot", "Steel Ingot")

#Tool.register(ID: str, name: str).level(lvl: int).timeFac(tf: float)

Tool.register("test_tool", "Test Tool").level(999999).timeFac(999999.0)

Tool.register("wooden_pickaxe", "Wooden Pickaxe").level(0).timeFac(0.5)
Tool.register("stone_pickaxe", "Stone Pickaxe").level(1).timeFac(1.5)
Tool.register("iron_pickaxe", "Iron Pickaxe").level(2).timeFac(1.0)

#Block.register(ID: str).drops(item: Item).level(lvl: int).time(t: int).rates(_min: int, _max: int, rate: float)

Block.register("stone").drops(Item.COBBLED_STONE).level(0).time(1.5).rates(1, 1, 1.0)
Block.register("coal").drops(Item.COAL).level(0).time(1).rates(1, 3, 0.2)
Block.register("iron").drops(Item.RAW_IRON).level(0).time(1.2).rates(1, 2, 0.07)
Block.register("copper").drops(Item.RAW_COPPER).level(0).time(1.2).rates(1, 2, 0.07)
Block.register("gold").drops(Item.RAW_GOLD).level(1).time(1.5).rates(1, 2, 0.07)
Block.register("aluminium").drops(Item.RAW_ALUMINIUM).level(1).time(1.8).rates(1, 2, 0.07)
Block.register("veridium").drops(Item.RAW_VERIDIUM).level(2).time(2.0).rates(1, 2, 0.07)
Block.register("titanium").drops(Item.RAW_TITANIUM).level(1).time(2.5).rates(1, 2, 0.07)

#Recipe.register(ID: str).inputs(i: list[Union[Item, tuple[Item, int]]]).outputs(o: list[Union[Item, tuple[Item, int]]]).time(t: float)

Recipe.register("iron_ingot").inputs([Item.RAW_IRON]).outputs([Item.IRON_INGOT]).time(1.2)
Recipe.register("copper_ingot").inputs([Item.RAW_COPPER]).outputs([Item.COPPER_INGOT]).time(1.2)
Recipe.register("brass_ingot").inputs([Item.IRON_INGOT, Item.COPPER_INGOT]).outputs([Item.BRASS_INGOT]).time(1.4)
Recipe.register("gold_ingot").inputs([Item.RAW_GOLD]).outputs([Item.GOLD_INGOT]).time(1.5)
Recipe.register("aluminium_ingot").inputs([Item.RAW_ALUMINIUM]).outputs([Item.ALUMINIUM_INGOT]).time(1.8)
Recipe.register("steel_ingot").inputs([(Item.IRON_INGOT, 2), Item.COAL]).outputs([Item.STEEL_INGOT]).time(2)
Recipe.register("veridium_ingot").inputs([Item.RAW_VERIDIUM]).outputs([Item.VERIDIUM_INGOT]).time(2.0)
Recipe.register("titanium_ingot").inputs([Item.RAW_TITANIUM, Item.COAL]).outputs([Item.TITANIUM_INGOT]).time(2.2)

#ResearchPoint.register(ID: str, name: str).costs(i: list[tuple[Item, int]], money: int).blocks(b: list[Block]).tools(t: list[Tool]).recipes(r: list[Recipe])

ResearchPoint.register("start", "Start") \
    .blocks([
        Block.COAL,
        Block.IRON,
        Block.COPPER,
        Block.STONE
    ]
    ).tools([
        Tool.WOODEN_PICKAXE,
        Tool.IRON_PICKAXE
    ]
    ).recipes([
        Recipe.IRON_INGOT,
        Recipe.COPPER_INGOT
    ]
    )

ResearchPoint.register("basics", "Basics") \
    .costs([
        (Item.COAL, 20),
        (Item.IRON_INGOT, 10)
    ], 200
    ).blocks([
        Block.GOLD,
        Block.ALUMINIUM,
        Block.VERIDIUM,
        Block.TITANIUM
    ]
    ).tools([
        Tool.IRON_PICKAXE
    ]
    ).recipes([
        Recipe.GOLD_INGOT,
        Recipe.ALUMINIUM_INGOT,
        Recipe.VERIDIUM_INGOT,
        Recipe.TITANIUM_INGOT
    ]
    )

ResearchPoint.research("start")