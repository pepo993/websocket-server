import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", 8080))  # 🔴 Porta WebSocket assegnata da Render
HTTP_PORT = 10001  # 🔴 Porta del server HTTP per l'Health Check di Render

async def handler(websocket, path):
    """
    Gestisce solo connessioni WebSocket e ignora richieste HTTP.
    """
    try:
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            print("⚠️ Richiesta HTTP ricevuta e ignorata")
            await websocket.close(code=1000)  # 🔴 Chiudiamo la connessione in modo pulito
            return

        print("✅ Nuova connessione WebSocket su /ws")
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")

    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """
    Avvia il server WebSocket su Render e accetta connessioni su /ws.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")

    await server.wait_closed()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Server HTTP per l'Health Check di Render, gestisce anche richieste HEAD.
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

    def do_HEAD(self):
        """
        Intercetta richieste HEAD e risponde con 200 OK.
        """
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def start_http_server():
    """
    Avvia un piccolo server HTTP per far contento Render.
    """
    server = HTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
    print(f"🌍 Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}/")
    server.serve_forever()

if __name__ == "__main__":
    try:
        # Avvia il server HTTP in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()
        
        # Avvia il WebSocket Server
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del server: {e}")

