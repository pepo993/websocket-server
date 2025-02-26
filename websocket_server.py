import asyncio
import json
import websockets
import os
import datetime
from game_logic import load_game_data
from aiohttp import web  # Per gestire richieste HTTP separatamente

# 📌 Render assegna automaticamente una porta tramite la variabile d'ambiente PORT
PORT = int(os.getenv("PORT", 8000))  # La porta WebSocket DEVE essere quella assegnata da Render
HTTP_PORT = 8080  # Porta per il server HTTP di health check
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato


async def notify_clients():
    """Invia aggiornamenti ai client WebSocket solo se lo stato cambia."""
    global ultimo_stato_trasmesso

    while True:
        if connected_clients:
            try:
                game_data = load_game_data()
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data["players"].values()),
                        "jackpot": len(game_data["players"]) * 1,
                        "giocatori_attivi": len(game_data["players"]),
                        "vincitori": game_data.get("winners", {})
                    },
                    "players": {
                        user_id: {"cartelle": game_data["players"][user_id]}
                        for user_id in game_data["players"]
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
                    except Exception as e:
                        print(f"⚠️ Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)

                for client in disconnected_clients:
                    connected_clients.remove(client)

            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")

        await asyncio.sleep(2)


async def websocket_handler(websocket, path):
    """Gestisce le connessioni WebSocket."""
    if path != "/ws":
        await websocket.close()
        return

    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "Sconosciuto"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"""
🔗 **Nuovo client connesso!**
📍 **IP:** {client_ip}
⏳ **Timestamp:** {timestamp}
👥 **Client totali connessi:** {len(connected_clients)}
""")

    try:
        async for _ in websocket:
            pass  # Mantiene la connessione attiva
    except websockets.exceptions.ConnectionClosed:
        print(f"🔴 Client {client_ip} disconnesso")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")


async def start_websocket_server():
    """Avvia il server WebSocket sulla porta fornita da Render."""
    server = await websockets.serve(
        websocket_handler,
        "0.0.0.0",
        PORT,  # 📌 Deve essere la porta assegnata da Render
        ping_interval=10,
        ping_timeout=20
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()


async def health_check(request):
    """Gestisce richieste di health check per Render."""
    return web.Response(text="OK", status=200)


async def start_http_server():
    """Avvia un server HTTP per il health check richiesto da Render."""
    app = web.Application()
    app.router.add_get("/", health_check)  # 🚀 NON aggiungere esplicitamente HEAD!
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    print(f"✅ HTTP Server avviato su http://0.0.0.0:{HTTP_PORT}")


async def main():
    """Avvia WebSocket e HTTP server in parallelo."""
    await asyncio.gather(start_websocket_server(), start_http_server(), notify_clients())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
