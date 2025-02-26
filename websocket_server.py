import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Ottieni la porta assegnata da Render
PORT = int(os.getenv("PORT", 8080))  # Se "PORT" non esiste, usa 8080 come default

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
    """Avvia il WebSocket Server sulla porta assegnata da Render"""
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Server HTTP per Render per evitare errori 502."""
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
    """Avvia un piccolo server HTTP per il check di Render"""
    http_port = 10001  # Render permette un solo servizio pubblico, quindi scegli una porta diversa
    try:
        server = HTTPServer(("0.0.0.0", http_port), HealthCheckHandler)
        print(f"🌍 Server HTTP avviato su http://0.0.0.0:{http_port}/")
        server.serve_forever()
    except OSError as e:
        print(f"⚠️ HTTP Server non avviato: {e}")

if __name__ == "__main__":
    try:
        # Avvia il server HTTP in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()

        # Avvia il WebSocket Server
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del server: {e}")
