import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", 10000))  # Render assegna automaticamente la porta

async def handler(websocket, path):
    """Gestisce connessioni WebSocket."""
    print("✅ Nuova connessione WebSocket")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """Avvia il server WebSocket sulla stessa porta del Web Server."""
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Server HTTP per Render (health check)."""
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"WebSocket Server Running")
        else:
            self.send_response(404)
            self.end_headers()

def start_http_server():
    """Avvia un piccolo server HTTP sulla stessa porta del WebSocket."""
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    print(f"🌍 Server HTTP avviato su http://0.0.0.0:{PORT}/")
    server.serve_forever()

if __name__ == "__main__":
    try:
        # Avvia il server HTTP in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()

        # Avvia il WebSocket Server
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del server: {e}")
