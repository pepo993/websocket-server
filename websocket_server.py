import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 🔴 Usa la porta assegnata da Render
WS_PORT = int(os.getenv("PORT", 8080))  # Render fornisce automaticamente la porta
HTTP_PORT = 10001  # 🔴 Porta fissa per l'health check (deve essere diversa da WS_PORT)

async def handler(websocket, path):
    """
    Gestisce solo connessioni WebSocket e ignora richieste HTTP.
    """
    print("✅ Nuova connessione WebSocket accettata!")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """
    Avvia il server WebSocket sulla porta fornita da Render.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        WS_PORT
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{WS_PORT}/")

    await server.wait_closed()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Server HTTP per l'Health Check di Render.
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
    Avvia un piccolo server HTTP per l'Health Check di Render.
    """
    try:
        server = HTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
        print(f"🌍 Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}/")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Errore nell'avvio del server HTTP: {e}")

if __name__ == "__main__":
    try:
        # Avvia il server HTTP per l'health check in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()
        
        # Avvia il WebSocket Server sulla porta fornita da Render
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
