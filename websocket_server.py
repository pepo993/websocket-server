import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", 8080))  # 🔴 Render assegna automaticamente la porta

async def handler(websocket, path):
    """
    Gestisce solo connessioni WebSocket e rifiuta richieste HTTP.
    """
    try:
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            print("❌ Connessione HTTP rifiutata (non è un WebSocket)")
            await websocket.close(code=4001)
            return

        print("✅ Nuova connessione WebSocket")
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")

    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """
    Avvia il server WebSocket.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",  # 🔴 Accetta connessioni pubbliche
        PORT
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")

    await server.wait_closed()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Un piccolo server HTTP per far contento Render.
    """
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
    """
    Avvia un piccolo server HTTP su una porta diversa per l'health check di Render.
    """
    http_port = 10000  # 🔴 Scegliamo una porta diversa da quella del WebSocket
    server = HTTPServer(("0.0.0.0", http_port), HealthCheckHandler)
    print(f"🌍 Server HTTP avviato su http://0.0.0.0:{http_port}/")
    server.serve_forever()

if __name__ == "__main__":
    try:
        # Avvia il server HTTP in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()
        
        # Avvia il WebSocket Server
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del server: {e}")

