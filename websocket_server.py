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
    """Gestisce connessioni WebSocket e ignora richieste HTTP."""
    try:
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            log_message("⚠️ Richiesta HTTP ricevuta e ignorata")
            return  # Ignora senza errori

        log_message(f"✅ Nuova connessione WebSocket accettata da {websocket.remote_address}")

        while True:
            try:
                message = await websocket.recv()
                log_message(f"📩 Messaggio ricevuto: {message}")

                response = f"Echo: {message}"
                await websocket.send(response)
                log_message(f"📤 Risposta inviata: {response}")

            except websockets.exceptions.ConnectionClosed as e:
                log_message(f"🔴 Connessione chiusa: codice {e.code}, motivo: {e.reason}")
                break  # Esce dal ciclo e chiude la connessione

            except Exception as e:
                log_message(f"⚠️ Errore durante la comunicazione WebSocket: {e}")
                await websocket.close(code=1011, reason=str(e))
                break  # Chiude la connessione dopo un errore

    except Exception as e:
        log_message(f"⚠️ Errore WebSocket durante la gestione della connessione: {e}")
        await websocket.close(code=1011, reason=str(e))

async def start_websocket():
    """Avvia il WebSocket Server."""
    try:
        server = await websockets.serve(handler, "0.0.0.0", PORT)
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

def start_http_server():
    """Avvia un piccolo server HTTP per l'health check di Render."""
    server = HTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
    log_message(f"🌍 Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}/ per Render")
    server.serve_forever()

if __name__ == "__main__":
    try:
        # Avvia il server HTTP in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()
        
        # Avvia il WebSocket Server
        asyncio.run(start_websocket())
    except Exception as e:
        log_message(f"❌ Errore nell'avvio del WebSocket Server: {e}")
