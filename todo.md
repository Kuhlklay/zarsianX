# Game System Design: Automation and Upgrade System
## Upgrade Tiers

**System Overview**: Players can unlock new recipes by progressing through upgrade tiers.

**Cost**: Each tier requires specific materials to unlock.

**Effect**: Unlocking a tier grants access to new recipes.

## Automation System

Machinery Types: Includes assembler, miner, etc.

**Command**: `auto <machinery-type> <recipe-name|resource> <amount>?1`

Initiates automation for a specified recipe or resource.

Optional `<amount>` defaults to 1 if not specified.

### Crafting Mechanics:
Machines are craftable items.

Starting an automation consumes the machine from the inventory.

Upon successful completion of the automation, the machine is returned to the inventory.

### Inventory Check:
Automation only proceeds if all required items for one crafting iteration are in the inventory.

Each automation is assigned a unique UUID.

## Automation Control Commands
### Commands
`auto stop <uuid>`: Stops the specified automation.

`auto pause <uuid>`: Pauses the specified automation.

`auto continue <uuid>` or `auto resume <uuid>`: Resumes the specified automation (both commands are equivalent).

## Listing Automations:
`auto list <uuid>?`: Displays all active/paused automations with:

Status (active/paused)

Progress (e.g., 1 / 15)

UUID

Machine type

Recipe name

If `<uuid>` is provided, only details for that automation are shown.

`auto recipe <recipe-name>`: Lists all automations using the specified recipe.



## Inventory Upgrades

**Upgrade Effect**: Certain tiers allow increasing the maximum inventory slots (maxSlots).

**Purpose**: Enhances player's capacity to hold items for crafting and automation.