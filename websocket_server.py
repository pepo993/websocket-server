import asyncio
import json
import websockets
import os
import datetime
from aiohttp import web  # Per il health check richiesto da Render

PORT = int(os.getenv("PORT", 10000))  # Render assegna la porta automaticamente
connected_clients = set()
ultimo_stato_trasmesso = None

async def notify_clients():
    """Invia aggiornamenti ai client WebSocket solo se lo stato cambia."""
    global ultimo_stato_trasmesso
    while True:
        if connected_clients:
            try:
                # Simuliamo dati di esempio (Sostituisci con il tuo `load_game_data()`)
                game_data = {
                    "drawn_numbers": [10, 20, 30],
                    "players": {"user1": ["cartella1"], "user2": ["cartella2"]},
                    "winners": {}
                }

                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data["players"].values()),
                        "jackpot": len(game_data["players"]) * 1,
                        "giocatori_attivi": len(game_data["players"]),
                        "vincitori": game_data.get("winners", {})
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
                    except Exception:
                        disconnected_clients.add(client)

                for client in disconnected_clients:
                    connected_clients.remove(client)

            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")

        await asyncio.sleep(2)

async def handler(websocket, path):
    """Gestisce connessioni WebSocket."""
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "Sconosciuto"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"🔗 Nuovo client connesso! IP: {client_ip} | {timestamp}")
    
    try:
        async for _ in websocket:
            pass
    except Exception:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")

async def start_websocket_server():
    """Avvia il server WebSocket su Render."""
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

async def health_check(request):
    """Risponde alle richieste di health check di Render."""
    return web.Response(text="OK", status=200)

async def start_http_server():
    """Avvia un server HTTP per il health check."""
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # Porta HTTP separata
    await site.start()
    print("✅ HTTP Server avviato su http://0.0.0.0:8080")

async def main():
    """Avvia WebSocket e server HTTP."""
    await asyncio.gather(start_websocket_server(), start_http_server(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
