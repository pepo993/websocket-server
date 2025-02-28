import asyncio
import json
import websockets
import os
from aiohttp import web
from game_logic import load_game_data

# Ottieni la porta assegnata da Railway
PORT = int(os.getenv("PORT", 8002))

# Set di client connessi
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

async def handler(websocket, path):
    """ Gestisce le connessioni WebSocket """
    connected_clients.add(websocket)
    print(f"Nuovo client connesso! Totale: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            print(f"Messaggio ricevuto: {message}")
            await websocket.send(json.dumps({"status": "ok", "message": "Connesso al WebSocket Server"}))
    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnesso normalmente.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Errore di connessione WebSocket: {e}")
    except Exception as e:
        print(f"Errore generale WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnesso! Totale attivi: {len(connected_clients)}")

async def notify_clients():
    """ Invio dati ai client WebSocket ogni 2 secondi """
    global ultimo_stato_trasmesso  
    while True:
        if connected_clients:
            try:
                game_data = load_game_data()
                if not game_data or "drawn_numbers" not in game_data:
                    print("Errore: Dati del gioco non validi.")
                    await asyncio.sleep(2)
                    continue  

                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data.get("players", {}).values()),
                        "jackpot": len(game_data.get("players", {})) * 1,
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "vincitori": game_data.get("winners", {})
                    },
                    "players": {
                        user_id: {"cartelle": game_data["players"][user_id]}
                        for user_id in game_data.get("players", {})
                    }
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
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)
                    except Exception as e:
                        print(f"Errore generico durante l'invio: {e}")
                        disconnected_clients.add(client)
                        
                for client in disconnected_clients:
                    connected_clients.remove(client)
                    
            except Exception as e:
                print(f"Errore generale in notify_clients: {e}")

        await asyncio.sleep(2)

# Endpoint di health check per Railway
async def health_check(request):
    return web.Response(text="OK", status=200)

# Configurazione del server HTTP per l'health check
app = web.Application()
app.router.add_get('/health', health_check)

async def start_server():
    # Rimuoviamo `subprotocols` per evitare il problema della negoziazione
    websocket_server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")

    # Avvia il server HTTP per l'health check
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # Porta 8080 per l'health check
    await site.start()
    print("Health check attivo su http://0.0.0.0:8080/health")

    await asyncio.gather(websocket_server.wait_closed(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"Errore nell'avvio del WebSocket Server: {e}")
