import time
import random

# --- Hilfsfunktionen zum Verwalten des Inventars ---
def add_item(inventory, item, amount=1, max_stack=15, max_slots=15):
    """
    Fügt dem Inventar 'amount' Stück von 'item' hinzu.
    Das Inventar besitzt maximal max_slots Slots, 
    wobei in jedem Slot bis zu max_stack gleiche Items gelagert werden können.
    """
    # Ist das Item bereits in einem Slot?
    if item in inventory:
        if inventory[item] + amount <= max_stack:
            inventory[item] += amount
            return True
        else:
            print(f"Kein Platz für mehr {item} in diesem Slot (maximal {max_stack} pro Slot).")
            return False
    else:
        if len(inventory) < max_slots:
            if amount <= max_stack:
                inventory[item] = amount
                return True
            else:
                print(f"Nicht genug Platz im Slot – maximal {max_stack} Stück möglich.")
                return False
        else:
            print("Keine freien Inventarslots mehr vorhanden.")
            return False

def remove_item(inventory, item, amount=1):
    """
    Entfernt 'amount' Stück von 'item' aus dem Inventar, sofern vorhanden.
    """
    if item in inventory:
        if inventory[item] < amount:
            print(f"Nicht genug {item} im Inventar.")
            return False
        else:
            inventory[item] -= amount
            if inventory[item] == 0:
                del inventory[item]
            return True
    else:
        print(f"Item '{item}' ist nicht im Inventar.")
        return False

# --- Hauptspiel ---
def main():
    # Spielbeschreibung und Einführung
    print("Willkommen beim Kohlenmienen-Abenteuer!")
    print("--------------------------------------------------")
    print("Du bist ein Abenteurer in einer Kohlenmine. Zunächst wählst du deinen Namen,")
    print("bekommst eine Spitzhacke und kannst dann Kohle abbauen. Dein Inventar")
    print("besitzt nun 15 Slots, wobei in jedem Slot maximal 5 identische Objekte Platz finden.")
    print("")
    print("Deine Begleiter:")
    print("  • Gustaf, der Verarbeiter - Er verwandelt 15 Kohle in 5 Hartkohle.")
    print("  • Anton, der Aufwerter - Er verbessert deine Spitzhacke. Mit 2 Hartkohle kannst du")
    print("    erstmals eine Verbesserung durchführen.")
    print("  • Vincent, der Verkäufer - Mit 1 Hartkohle stellst du eine Antiquität her,")
    print("    deren Seltenheit zufällig von 'Gewöhnlich' bis 'Sehr selten' reicht.")
    print("")
    print("Außerdem: Möchtest du direkt in die Eisenmine wechseln, so kostet die Reise 3")
    print("Hartkohle. In der Eisenmine baust du dann Eisen ab statt Kohle.")
    print("--------------------------------------------------")
    
    # Spieler gibt seinen Namen ein
    player_name = input("Bitte gib deinen Namen ein: ").strip()
    
    # Spieler-Status: Name, Inventar, Hartkohle, Spitzhacken-Level (0 = Holz, 1 = Upgrade, …)
    player = {
        "name": player_name,
        "inventory": {},      # z. B. {"Kohle": 3}
        "hartkohle": 0,
        "pickaxe_index": 0,   # 0: Holz, 1: (Upgrade, ursprünglich 'Stein'/nun gemäß Wunsch erste Verbesserung), 2: Eisen, 3: Gold, 4: Diamant
        "location": "Kohlenmine"
    }
    
    print(f"\nHallo {player['name']}, dein Abenteuer beginnt in der Kohlenmine.")
    
    # Definiere die Spitzhacken und die entsprechenden Mining-Zeiten (in Sekunden)
    pickaxe_levels = ["Holz", "Stein", "Eisen", "Gold", "Diamant"]
    # Angepasste Zeiten: 
    # - Holzspitzhacke: vorher 20, jetzt 10 Sekunden
    # - Erster Upgrade-Schritt (ehemals Stein, laut Wunsch als 'eisenspitzhacke' mit Miningzeit 12 -> 8) 
    #   soll nun in 8 Sekunden abbauen.
    # Die weiteren Werte bleiben unverändert.
    mining_times = [10, 8, 8, 6, 4]
    
    # Upgrade-Kosten: Für Upgrades von Level 0->1, 1->2, 2->3, 3->4
    upgrade_costs = [2, 3, 4, 5]
    
    # Spielschleife
    while True:
        command = input("\nBefehl (tipp 'help' für Befehle): ").strip().lower()
        
        if command in ["exit", "quit"]:
            print("Tschüss und viel Spaß beim nächsten Mal!")
            break
        
        elif command == "help":
            print("\nVerfügbare Befehle:")
            print("  mine                   - Baue in der aktuellen Mine (Kohle oder Eisen) ab.")
            print("  inventory              - Zeige dein aktuelles Inventar.")
            print("  status                 - Zeige deinen aktuellen Status.")
            print("  talk gustaf            - Rede mit Gustaf (Verarbeiter).")
            print("  talk anton             - Rede mit Anton (Aufwerter).")
            print("  talk vincent           - Rede mit Vincent (Verkäufer/Antiquitäten).")
            print("  travel [ziel]          - Reise zu 'kohlenmine' oder 'eisenmine'.")
            print("  exit                   - Beenden des Spiels.")
        
        elif command == "status":
            print("\n--- Spielerstatus ---")
            print("Name       :", player["name"])
            print("Standort   :", player["location"])
            print("Spitzhacke :", pickaxe_levels[player["pickaxe_index"]])
            print("Miningzeit :", mining_times[player["pickaxe_index"]], "Sekunden pro Abbau")
            print("Hartkohle  :", player["hartkohle"])
            if player["inventory"]:
                print("Inventar   :")
                for item, count in player["inventory"].items():
                    print(f"  {item}: {count}")
            else:
                print("Inventar   : leer")
        
        elif command == "inventory":
            print("\n--- Inventar ---")
            if not player["inventory"]:
                print("Dein Inventar ist leer.")
            else:
                for item, count in player["inventory"].items():
                    print(f"{item}: {count}")
        
        elif command.startswith("travel"):
            parts = command.split()
            if len(parts) < 2:
                print("Bitte gib das Reiseziel an: 'kohlenmine' oder 'eisenmine'.")
                continue
            destination = parts[1]
            if destination == "kohlenmine":
                if player["location"].lower() == "kohlenmine":
                    print("Du bist bereits in der Kohlenmine.")
                else:
                    player["location"] = "Kohlenmine"
                    print("Du reist zurück in die Kohlenmine.")
            elif destination == "eisenmine":
                if player["location"].lower() == "eisenmine":
                    print("Du bist bereits in der Eisenmine.")
                else:
                    if player["hartkohle"] >= 3:
                        player["hartkohle"] -= 3
                        player["location"] = "Eisenmine"
                        print("Du hast 3 Hartkohle bezahlt und reist in die Eisenmine.")
                    else:
                        print("Du hast nicht genug Hartkohle, um in die Eisenmine zu reisen (benötigt 3).")
            else:
                print("Unbekanntes Reiseziel. Möglich sind: kohlenmine, eisenmine.")
        
        elif command == "mine":
            # Je nach Standort wird abgebaut: In der Kohlenmine erhält man Kohle, in der Eisenmine Eisen.
            if player["location"].lower() == "kohlenmine":
                resource = "Kohle"
            elif player["location"].lower() == "eisenmine":
                resource = "Eisen"
            else:
                resource = "Unbekannt"
            
            # Direkte Check: Versuche, das abgebaute Item ins Inventar zu legen.
            current_pickaxe = pickaxe_levels[player["pickaxe_index"]]
            mining_time = mining_times[player["pickaxe_index"]]
            print(f"Du beginnst mit deiner {current_pickaxe}spitzhacke zu minen. Das dauert {mining_time} Sekunden...")
            time.sleep(mining_time)
            print(f"Du hast 1 {resource} abgebaut!")
            if not add_item(player["inventory"], resource, 1):
                print("Dein abgebautes Resource konnte nicht ins Inventar gelegt werden.")
        
        elif command == "talk gustaf":
            # Gustafs Aufgabe: Verarbeiten von 15 Kohle in 5 Hartkohle.
            coal_count = player["inventory"].get("Kohle", 0)
            if coal_count < 15:
                print("Gustaf: Bring mir 15 Stück Kohle, damit ich sie verarbeiten kann.")
            else:
                # Entferne 15 Kohle und erhalte 5 Hartkohle
                player["inventory"].pop("Kohle")
                hart_from_coal = 5
                player["hartkohle"] += hart_from_coal
                print(f"Gustaf: Ich habe deine 15 Kohle verarbeitet und dir {hart_from_coal} Hartkohle gegeben.")
        
        elif command == "talk anton":
            # Anton kann deine Spitzhacke upgraden.
            if player["pickaxe_index"] >= len(pickaxe_levels) - 1:
                print("Anton: Deine Spitzhacke ist bereits auf dem höchsten Stand.")
            else:
                cost = upgrade_costs[player["pickaxe_index"]]
                current_level = pickaxe_levels[player["pickaxe_index"]]
                next_level = pickaxe_levels[player["pickaxe_index"] + 1]
                print(f"Anton: Um deine {current_level}spitzhacke zu einer {next_level}spitzhacke aufzuwerten, benötigst du {cost} Hartkohle.")
                if player["hartkohle"] >= cost:
                    confirm = input("Möchtest du upgraden? (ja/nein): ").strip().lower()
                    if confirm == "ja":
                        player["hartkohle"] -= cost
                        player["pickaxe_index"] += 1
                        print(f"Anton: Sehr gut, deine Spitzhacke wurde auf {next_level} aufgewertet!")
                        print(f"Ab jetzt dauert es nur noch {mining_times[player['pickaxe_index']]} Sekunden pro Abbau.")
                    else:
                        print("Anton: In Ordnung, überlege es dir in Ruhe.")
                else:
                    print("Anton: Du hast nicht genügend Hartkohle für ein Upgrade.")
        
        elif command == "talk vincent":
            # Vincent: Mit 1 Hartkohle stellst du eine Antiquität her.
            if player["hartkohle"] < 1:
                print("Vincent: Du brauchst mindestens 1 Hartkohle, um eine Antiquität herzustellen.")
            else:
                confirm = input("Vincent: Möchtest du 1 Hartkohle investieren, um eine Antiquität herzustellen? (ja/nein): ").strip().lower()
                if confirm == "ja":
                    player["hartkohle"] -= 1
                    chance = random.random()
                    if chance < 0.6:
                        rarity = "Gewöhnlich"
                    elif chance < 0.85:
                        rarity = "Ungewöhnlich"
                    elif chance < 0.95:
                        rarity = "Selten"
                    else:
                        rarity = "Sehr selten"
                    print(f"Vincent: Geschafft! Du hast eine {rarity} Antiquität hergestellt. Ich verkaufe sie zu einem guten Preis!")
                else:
                    print("Vincent: Vielleicht später, wenn du es dir anders überlegst.")
        
        else:
            print("Unbekannter Befehl. Tipp 'help' für eine Übersicht.")

if __name__ == "__main__":
    main()
