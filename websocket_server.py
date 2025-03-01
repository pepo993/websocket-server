import os
import json
import asyncio
import websockets
from database import connect_db
from aiohttp import web
import sys

# Aggiunge il percorso della cartella corrente per trovare database.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import connect_db  # Ora Python dovrebbe trovarlo
# Ottieni la porta assegnata da Railway
PORT = int(os.getenv("PORT", 8002))

# Set di client connessi
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

def get_game_data():
    """Recupera lo stato del gioco dal database SQLite."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT game_active, drawn_numbers FROM game_state ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        game_active, drawn_numbers = row
        return {
            "game_active": bool(game_active),
            "drawn_numbers": json.loads(drawn_numbers)
        }
    
    return {"game_active": False, "drawn_numbers": []}

def get_players_data():
    """Recupera i giocatori e le loro cartelle dal database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, cartelle FROM players")
    players = {}

    for user_id, cartelle in cursor.fetchall():
        players[user_id] = {"cartelle": json.loads(cartelle)}

    return players

async def notify_clients():
    """Invia aggiornamenti ai client WebSocket solo se ci sono nuove informazioni."""
    global ultimo_stato_trasmesso  

    while True:
        if connected_clients:
            try:
                game_data = get_game_data()
                players_data = get_players_data()

                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p["cartelle"]) for p in players_data.values()),
                        "jackpot": sum(len(p["cartelle"]) for p in players_data.values()),
                        "giocatori_attivi": len(players_data),
                    },
                    "players": players_data
                }

                if stato_attuale == ultimo_stato_trasmesso:
                    await asyncio.sleep(2)
                    continue  

                ultimo_stato_trasmesso = stato_attuale
                message = json.dumps(stato_attuale)

                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except Exception as e:
                        print(f"⚠️ Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)

                for client in disconnected_clients:
                    connected_clients.remove(client)

            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")

        await asyncio.sleep(2)

async def handler(websocket):
    """Gestisce le connessioni WebSocket con la WebApp."""
    connected_clients.add(websocket)

    client_ip = websocket.remote_address[0] if websocket.remote_address else "Sconosciuto"
    print(f"✅ Nuovo client connesso! IP: {client_ip}")

    try:
        async for _ in websocket:
            pass  # Mantiene la connessione attiva
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale attivi: {len(connected_clients)}")

async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_server():
    """Avvia il WebSocket server e il sistema di health check per Railway."""
    server = await websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None, ping_timeout=None)
    print(f"🚀 WebSocket Server avviato su ws://0.0.0.0:{PORT}")

    # Health Check per Railway
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ Health check attivo su http://0.0.0.0:8080/health")

    await asyncio.gather(server.wait_closed(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
