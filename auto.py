import uuid
from enum import Enum
from typing import List, Dict
from registry import Item, Recipe

class LocID:
    def __init__(self, name: str):
        self.name = name

MachineStatus = Enum('MachineStatus', "ACTIVE PAUSED STOPPED")

class Machine:
    def __init__(self, machineType: str, recipe: Recipe, loc: LocID):
        self.uuid = str(uuid.uuid4())
        self.type = machineType
        self.recipe = recipe
        self.loc = loc
        self.status = MachineStatus.ACTIVE
        self.inputs: List[Connection] = []
        self.outputs: List[Connection] = []
        self.inventory: Dict[str, int] = {}  # Resource type -> quantity

    def process(self) -> None:
        if self.status != MachineStatus.ACTIVE:
            return
        # Check if inputs are available and process the recipe
        if self.canProcess():
            self.pull()
            self.produce()

    def canProcess(self) -> bool:
        # Check if all required inputs are available
        for input_res, qty in self.recipe.inputs.items():
            if self.inventory.get(input_res, 0) < qty:
                return False
        return True

    def pull(self) -> None:
        # Pull items from connected machines
        for conn in self.inputs:
            if conn.source and conn.source.inventory.get(conn.resourceType, 0) > 0:
                self.inventory[conn.resourceType] = self.inventory.get(conn.resourceType, 0) + 1
                conn.source.inventory[conn.resourceType] -= 1

    def produce(self) -> None:
        # Produce outputs based on recipe
        for outputRes, qty in self.recipe.outputs.items():
            self.inventory[outputRes] = self.inventory.get(outputRes, 0) + qty

    def stop(self) -> None:
        self.status = MachineStatus.STOPPED

    def pause(self) -> None:
        self.status = MachineStatus.PAUSED

    def resume(self) -> None:
        self.status = MachineStatus.ACTIVE

    def info(self) -> Dict:
        return {
            "uuid": self.uuid,
            "type": self.type,
            "recipe": self.recipe.name,
            "status": self.status.value,
            "inputs": [(conn.source.uuid if conn.source else None, conn.resource_type) for conn in self.inputs],
            "outputs": [(conn.target.uuid if conn.target else None, conn.resource_type) for conn in self.outputs]
        }

class Connection:
    def __init__(self, source: Machine, target: Machine, resourceType: Item):
        self.source = source
        self.target = target
        self.resourceType = resourceType

# Miners are special, they take a ressource instead of a recipe
class Miner(Machine):
    def __init__(self, recipe: Recipe, loc: LocID):
        super().__init__("miner", recipe, loc)
        self.inputs = []  # Miners have 0 inputs
        self.outputs = [None]  # 1 output slot

class Constructor(Machine):
    def __init__(self, recipe: Recipe, loc: LocID):
        super().__init__("constructor", recipe, loc)
        self.inputs = [None] * 2  # 2 input slots
        self.outputs = [None]  # 1 output slot

class Assembler(Machine):
    def __init__(self, recipe: Recipe, loc: LocID):
        super().__init__("assembler", recipe, loc)
        self.inputs = [None] * 3  # 3 input slots
        self.outputs = [None]  # 1 output slot

class Storage(Machine):
    def __init__(self, resourceType: Item, loc: LocID):
        super().__init__("storage", None, loc)
        self.inventory = {resourceType: 0}  # ResourceType
        self.resourceType = resourceType
        self.inputs = []  # Unlimited inputs
        self.outputs = []  # Unlimited outputs

    def addInput(self, conn: Connection) -> None:
        self.inputs.append(conn)  # No limit on inputs

    def addOutput(self, conn: Connection) -> None:
        self.outputs.append(conn)  # No limit on outputs

    def removeInput(self, conn: Connection) -> None:
        self.inputs.remove(conn)

    def removeOutput(self, conn: Connection) -> None:
        self.outputs.remove(conn)

    def add(self, amount: int = 1) -> Dict[Item, int]:
        self.inventory[self.resourceType] += amount
        return {self.resourceType: amount}

    def take(self, amount: int = 1) -> Dict[Item, int]:
        if self.resourceType in self.inventory:
            taken = min(amount, self.inventory[self.resourceType])
            self.inventory[self.resourceType] -= taken
            return {self.resourceType: taken}
        return {}