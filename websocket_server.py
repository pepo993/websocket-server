import asyncio
import websockets
import os
import threading
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configurazione delle porte
PORT = int(os.getenv("PORT", 8080))  # Porta WebSocket assegnata da Render
HTTP_PORT = 10001  # Porta per l'Health Check di Render

def log_message(message):
    """Genera log con timestamp per debugging"""
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

async def handler(websocket, path):
    """Gestisce connessioni WebSocket e rifiuta richieste HTTP non valide."""
    try:
        # Controlla se la richiesta è effettivamente WebSocket
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            log_message("⚠️ Connessione HTTP non valida rifiutata.")
            await websocket.close(code=4001, reason="Non è una connessione WebSocket")
            return

        log_message(f"✅ Connessione WebSocket accettata da {websocket.remote_address}")

        async for message in websocket:
            log_message(f"📩 Messaggio ricevuto: {message}")
            response = f"Echo: {message}"
            await websocket.send(response)
            log_message(f"📤 Risposta inviata: {response}")

    except websockets.exceptions.ConnectionClosed as e:
        log_message(f"🔴 Connessione chiusa: codice {e.code}, motivo: {e.reason}")

    except Exception as e:
        log_message(f"⚠️ Errore WebSocket: {e}")
        await websocket.close(code=1011, reason=str(e))

async def start_websocket():
    """Avvia il WebSocket Server con gestione degli errori."""
    try:
        server = await websockets.serve(
            handler,
            "0.0.0.0",
            PORT,
            ping_interval=None,  # Disabilita il timeout del ping
            ping_timeout=None
        )
        log_message(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/")
        await server.wait_closed()
    except Exception as e:
        log_message(f"❌ Errore nell'avvio del WebSocket Server: {e}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Server HTTP per l'Health Check di Render."""
    def do_GET(self):
        if self.path == "/":
            log_message("✅ Health Check ricevuto - Server attivo")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"WebSocket Server Running")
        else:
            log_message(f"⚠️ Richiesta HTTP sconosciuta: {self.path}")
            self.send_response(404)
            self.end_headers()

    def do_HEAD(self):
        """Gestisce richieste HEAD per evitare errori su Render"""
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def start_http_server():
    """Avvia un piccolo server HTTP per l'health check di Render."""
    server = HTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
    log_message(f"🌍 Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}/ per Render")
    server.serve_forever()

if __name__ == "__main__":
    try:
        threading.Thread(target=start_http_server, daemon=True).start()  # Avvia il server HTTP
        asyncio.run(start_websocket())  # Avvia il WebSocket Server
    except Exception as e:
        log_message(f"❌ Errore nell'avvio del WebSocket Server: {e}")
