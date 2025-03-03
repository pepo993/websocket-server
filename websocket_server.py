import os
import json
import asyncio
import websockets
from aiohttp import web
from config import COSTO_CARTELLA

# Assicura che la cartella "data/" esista
os.makedirs("data", exist_ok=True)

# Percorso del file di stato
game_data_path = os.path.join("data", "game_data.json")

# Porta assegnata per Railway
PORT = int(os.getenv("PORT", 8002))

# Set di client connessi
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

# 📌 Funzione per caricare lo stato del gioco
def load_game_state():
    if os.path.exists(game_data_path):
        with open(game_data_path, "r") as f:
            return json.load(f)
    return {"drawn_numbers": [], "players": {}, "winners": {}}

# 📌 Funzione per salvare lo stato di gioco
def save_game_state(state):
    with open(game_data_path, "w") as f:
        json.dump(state, f, indent=4)

# 📌 Gestione delle connessioni WebSocket
async def handler(websocket):
    """ Gestisce le connessioni WebSocket """
    connected_clients.add(websocket)
    print(f"✅ Nuovo client connesso! Totale: {len(connected_clients)}")
    print(f"✅ Nuovo client connesso: {websocket.remote_address}")  # Stampa IP e porta del client
    try:
        async for message in websocket:
            print(f"📥 Messaggio ricevuto: {message}")
            
            try:
                game_state = json.loads(message)
                if "drawn_numbers" in game_state:
                    save_game_state(game_state)  # ✅ Salva lo stato aggiornato
                    print("📌 Stato del gioco aggiornato con nuovi numeri estratti.")
                    
                    # 📢 Invia l'aggiornamento a tutti i client connessi
                    broadcast_message = json.dumps(game_state)
                    disconnected_clients = set()

                    for client in connected_clients:
                        try:
                            await client.send(broadcast_message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(client)

                    # Rimuove i client disconnessi
                    for client in disconnected_clients:
                        connected_clients.discard(client)
                        print(f"❌ Client disconnesso rimosso. Totale attivi: {len(connected_clients)}")

            except json.JSONDecodeError:
                print("❌ Errore: Messaggio non è un JSON valido.")

    except websockets.exceptions.ConnectionClosed:
        print("⚠️ Client disconnesso normalmente.")
    finally:
        if websocket in connected_clients:
            connected_clients.discard(websocket)
            print(f"❌ Client rimosso dalla lista. Totale attivi: {len(connected_clients)}")

# 📌 Funzione per notificare i client attivi
import time

async def notify_clients():
    """ Invia aggiornamenti ai client solo se lo stato è cambiato """
    global ultimo_stato_trasmesso

    while True:
        if connected_clients:
            try:
                game_data = load_game_state()

                await asyncio.sleep(0.2)  # Evita spam di aggiornamenti

                if not game_data or "drawn_numbers" not in game_data:
                    print("❌ Dati di gioco non validi.")
                    await asyncio.sleep(3)
                    continue  

                # 🎲 Recupera o genera un ID partita **solo se non esiste già**
                if "game_id" not in game_data:
                    game_data["game_id"] = str(int(time.time() * 1000))  # Usa timestamp solo alla creazione



                # 🕐 Imposta il tempo della prossima partita (2 minuti dopo la fine)
                if "next_game_time" not in game_data or game_data["next_game_time"] < int(time.time() * 1000):
                    game_data["next_game_time"] = int((time.time() + 120) * 1000)  # 2 minuti dopo

                save_game_state(game_data)  # Salviamo lo stato con game_id fisso
                
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data.get("players", {}).values()),
                        "jackpot": sum(len(p) for p in game_data.get("players", {}).values()) * COSTO_CARTELLA,
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "vincitori": game_data.get("winners", {}),
                        "next_game_time": game_data["next_game_time"],  # ⏳ Countdown partita
                        "game_id": game_data["game_id"]  # 🎲 ID partita fisso
                    },
                    "players": {
                        user_id: {"cartelle": game_data["players"][user_id]}
                        for user_id in game_data.get("players", {})
                    }
                }

                print(f"📤 Dati inviati ai client WebSocket: {json.dumps(stato_attuale, indent=None, separators=(', ', ': '))}")
                # 📌 Evita di inviare aggiornamenti duplicati
                if stato_attuale == ultimo_stato_trasmesso:
                    await asyncio.sleep(3)
                    continue  
                    
                # ✅ Aggiorniamo lo stato trasmesso solo se è cambiato
                ultimo_stato_trasmesso = json.loads(json.dumps(stato_attuale))  # Deep copy
                #print(f"📤 DEBUG:Stato del gioco inviato: {json.dumps(stato_attuale, indent=None, separators=(', ', ': '))}")
                message = json.dumps(stato_attuale) # Convertiamo lo stato in JSON

                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        print(f"❌ Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)

                # 📌 Rimuove i client disconnessi
                for client in disconnected_clients:
                    connected_clients.discard(client)
                    print(f"❌ Client disconnesso rimosso. Totale attivi: {len(connected_clients)}")

            except Exception as e:
                print(f"❌ Errore in notify_clients: {e}")

        await asyncio.sleep(2)  # Mantiene un intervallo di aggiornamento di 2s

# 📌 Health Check per Railway
async def health_check(request):
    return web.Response(text="OK", status=200)

# Configura il server HTTP per l'health check
app = web.Application()
app.router.add_get('/health', health_check)

# 📌 Avvio del WebSocket Server
async def start_server():
    websocket_server = await websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None, ping_timeout=None)

    print(f"🚀 WebSocket Server avviato su ws://0.0.0.0:{PORT}")

    # Avvia il server HTTP per l'health check
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ Health check attivo su http://0.0.0.0:8080/health")

    await asyncio.gather(websocket_server.wait_closed(), notify_clients())

# 📌 Avvio del server
if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
