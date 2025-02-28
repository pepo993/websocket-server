import os
import asyncio
import json
import websockets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from game_logic import load_game_data

connected_clients = set()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Server HTTP per rispondere ai controlli di stato di Render.
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

def start_health_check_server():
    """
    Avvia un server HTTP sulla porta 8080 per rispondere alle richieste di Render.
    """
    server = HTTPServer(("0.0.0.0", 8080), HealthCheckHandler)
    print("✅ Health Check Server avviato su http://0.0.0.0:8080/")
    server.serve_forever()

async def handler(websocket, path):
    """
    Accetta SOLO connessioni WebSocket su `/ws`.
    """
    if path != "/ws":
        print(f"❌ Connessione rifiutata: {path} non è un WebSocket valido")
        await websocket.close()
        return

    connected_clients.add(websocket)
    print(f"✅ Nuovo client connesso! Totale: {len(connected_clients)}")

    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(json.dumps({"response": "Messaggio ricevuto"}))
    except websockets.ConnectionClosed:
        print("🔴 Connessione WebSocket chiusa")
    finally:
        connected_clients.remove(websocket)
        print(f"🔌 Client disconnesso! Totale attivi: {len(connected_clients)}")

async def main():
    """
    Avvia il WebSocket Server e il Health Check Server.
    """
    PORT = int(os.environ.get("PORT", 10000))

    threading.Thread(target=start_health_check_server, daemon=True).start()

    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT,
        subprotocols=["binary"]
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())


