import os
import json
import asyncio
import websockets
from aiohttp import web
from config import COSTO_CARTELLA
# Assicura che la cartella "data/" esista
os.makedirs("data", exist_ok=True)

# Percorso unificato per il file di stato
game_data_path = os.path.join("data", "game_data.json")

# Ottieni la porta assegnata da Railway
PORT = int(os.getenv("PORT", 8002))

# Set di client connessi
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

# Funzione per caricare lo stato di gioco
def load_game_state():
    if os.path.exists(game_data_path):
        with open(game_data_path, "r") as f:
            return json.load(f)
    return {"drawn_numbers": [], "players": {}, "winners": {}}

# Funzione per salvare lo stato di gioco
def save_game_state(state):
    with open(game_data_path, "w") as f:
        json.dump(state, f, indent=4)

async def handler(websocket):
    """ Gestisce le connessioni WebSocket """
    connected_clients.add(websocket)
    print(f"✅ Nuovo client connesso! Totale: {len(connected_clients)}")

    try:
        async for message in websocket:
            print(f"📥 Messaggio ricevuto: {message}")
            
            # Verifica se il messaggio contiene dati di aggiornamento dal bot Telegram
            try:
                game_state = json.loads(message)
                if "drawn_numbers" in game_state:  # Controlla che sia un aggiornamento valido
                    save_game_state(game_state)  # ✅ Salva il nuovo stato ricevuto dal bot
                    print("📌 Stato di gioco aggiornato con nuovi numeri estratti.")
                    
                    # Invia il nuovo stato a tutti i client connessi
                    broadcast_message = json.dumps(game_state)
                    for client in connected_clients:
                        await client.send(broadcast_message)

            except json.JSONDecodeError:
                print("❌ Errore: Messaggio ricevuto non è un JSON valido.")
            
            await websocket.send(json.dumps({"status": "ok", "message": "Messaggio ricevuto"}))
    
    except websockets.exceptions.ConnectionClosedOK:
        print("⚠️ Client disconnesso normalmente.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ Errore di connessione WebSocket: {e}")
    except Exception as e:
        print(f"❌ Errore generale WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"❌ Client disconnesso! Totale attivi: {len(connected_clients)}")

async def notify_clients():
    """ Invia i dati ai client WebSocket solo se lo stato è cambiato """
    global ultimo_stato_trasmesso  
    while True:
        if connected_clients:
            try:
                game_data = load_game_state()
                if not game_data or "drawn_numbers" not in game_data:
                    print("❌ Errore: Dati del gioco non validi.")
                    await asyncio.sleep(5)
                    continue  

                # Costruisce lo stato attuale del gioco
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data.get("players", {}).values()),
                        "jackpot": sum(len(p) for p in game_data.get("players", {}).values()) * COSTO_CARTELLA,
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "vincitori": game_data.get("winners", {})
                    },
                    "players": {
                        user_id: {"cartelle": game_data["players"][user_id]}
                        for user_id in game_data.get("players", {})
                    }
                }

                # ✅ Controllo duplicati PRIMA di stampare e inviare ai client
                if stato_attuale == ultimo_stato_trasmesso:
                    print(f"⚠️ Stato invariato, evitando duplicati. Ultimo numero estratto: {stato_attuale['numero_estratto']}")
                    await asyncio.sleep(10)  # ⏳ Aumentiamo il tempo per ridurre il carico
                    continue  

                # ✅ Aggiorniamo lo stato trasmesso solo se è cambiato
                ultimo_stato_trasmesso = json.loads(json.dumps(stato_attuale))  # Copia profonda dello stato                
                print(f"📤 DEBUG:Stato del gioco inviato: {json.dumps(stato_attuale, indent=None, separators=(', ', ': '))}")


                # Convertiamo lo stato in JSON
                message = json.dumps(stato_attuale)

                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"❌ Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)
                    except Exception as e:
                        print(f"❌ Errore generico durante l'invio: {e}")
                        disconnected_clients.add(client)
                        
                # Rimuove i client disconnessi
                for client in disconnected_clients:
                    connected_clients.remove(client)

            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")

        await asyncio.sleep(2)  # Manteniamo l'intervallo a 2 secondi per reattività


# Endpoint di health check per Railway
async def health_check(request):
    return web.Response(text="OK", status=200)

# Configurazione del server HTTP per l'health check
app = web.Application()
app.router.add_get('/health', health_check)

async def start_server():
    # Creiamo il server WebSocket con il parametro `path` corretto
    websocket_server = await websockets.serve(handler, "0.0.0.0", PORT, ping_interval=30, ping_timeout=30)

    print(f"🚀 WebSocket Server avviato su ws://0.0.0.0:{PORT}")

    # Avvia il server HTTP per l'health check
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # Porta 8080 per l'health check
    await site.start()
    print("✅ Health check attivo su http://0.0.0.0:8080/health")

    await asyncio.gather(websocket_server.wait_closed(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")


