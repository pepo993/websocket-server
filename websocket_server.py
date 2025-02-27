import os
import asyncio
import json
import websockets
import datetime
from game_logic import load_game_data
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Server HTTP semplice per rispondere ai controlli di stato di Render.
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_check_server():
    """
    Avvia un piccolo server HTTP sulla porta 8080 per il health check di Render.
    """
    server = HTTPServer(("0.0.0.0", 8080), HealthCheckHandler)
    print("✅ Health Check Server avviato su http://0.0.0.0:8080/")
    server.serve_forever()

async def handler(websocket, path):
    """
    Gestisce le connessioni WebSocket con la WebApp.
    """
    if path != "/ws":
        print("❌ Connessione rifiutata: percorso non valido")
        await websocket.close()
        return

    connected_clients.add(websocket)
    print(f"🔗 Nuovo client connesso! Totale client attivi: {len(connected_clients)}")

    try:
        async for _ in websocket:
            pass  # Mantiene la connessione aperta
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")

async def main():
    """
    Avvia il WebSocket Server e il Health Check Server.
    """
    PORT = int(os.environ.get("PORT", 8002))

    # Avvia il server HTTP per il health check in un thread separato
    threading.Thread(target=start_health_check_server, daemon=True).start()

    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
