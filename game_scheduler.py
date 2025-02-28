import random
import asyncio
from game_logic import load_game_data, save_game_data, start_game, check_winners

async def draw_numbers():
    while True:
        try:
            print("🔄 Controllo partita...")
            game_data = load_game_data()

            if not isinstance(game_data, dict) or "game_active" not in game_data:
                print("⚠️ Errore nel file game_data.json. Resettando i dati...")
                game_data = {"game_active": False, "drawn_numbers": []}
                save_game_data(game_data)

            # 🚨 Se il gioco non è attivo, avvialo automaticamente
            if not game_data["game_active"]:
                print("⏸️ Il gioco non è attivo! Avvio una nuova partita...")
                game_data["game_active"] = True
                game_data["drawn_numbers"] = []
                save_game_data(game_data)
                start_game()
                print("✅ Nuova partita avviata!")
                await asyncio.sleep(10)  # Breve attesa prima della prima estrazione
                continue  

            print(f"🎰 Partita attiva, numeri estratti finora: {len(game_data['drawn_numbers'])}/90")

            # 🏆 Controlla se ci sono vincitori
            winners = check_winners(game_data)

            if winners["Cinquina"]:
                print(f"🏆 Cinquina vinta da: {winners['Cinquina']}")

            if winners["Bingo"]:
                print(f"🎉 Partita terminata! Vincitori del Bingo: {winners['Bingo']}")
                save_game_data(game_data)
                await asyncio.sleep(60) # Aspetta 1 minuto prima di riavviare la partita
                continue  

            # 🚨 Se tutti i numeri sono stati estratti, termina la partita
            if len(game_data["drawn_numbers"]) >= 90:
                print("🏆 Tutti i numeri sono stati estratti, la partita è finita!")
                game_data["game_active"] = False  # 🔴 FERMA IL GIOCO
                save_game_data(game_data)
                print("🔄 In attesa di riavvio della partita...")
                await asyncio.sleep(60)  # Aspetta 1 minuto prima di riavviare la partita
                continue  

            # 🔢 Estrai un numero disponibile
            numeri_disponibili = list(set(range(1, 91)) - set(game_data["drawn_numbers"]))

            if numeri_disponibili:
                num = random.choice(numeri_disponibili)
                game_data["drawn_numbers"].append(num)
                save_game_data(game_data)
                print(f"✅ Numero estratto: {num}")
            else:
                print("⚠️ Nessun numero disponibile da estrarre!")

            await asyncio.sleep(8)  # 🔴 Ora estraiamo un numero ogni 8 secondi

        except Exception as e:
            print(f"❌ Errore nel loop di estrazione: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(draw_numbers())
        print("✅ Il gioco è attivo!")
        loop.run_forever()
    except Exception as e:
        print(f"❌ Errore nell'avvio del game scheduler: {e}")
