import asyncio
import json
import os
from flask import Flask
import threading
import websockets

PORT = int(os.getenv("PORT", 10000))  # Usa la porta di Render
connected_clients = set()

# Creazione del server Flask per gestire richieste HTTP
app = Flask(__name__)

@app.route('/')
def home():
    return "WebSocket Server is Running!", 200  # Messaggio di test per Render

async def handler(websocket, path):
    """Gestisce connessioni WebSocket e ignora richieste HTTP."""
    if "Upgrade" not in websocket.request_headers:
        print("⚠️ Richiesta HTTP ricevuta e ignorata")
        return  # Ignora richieste HTTP

    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("🔴 Connessione chiusa")
    finally:
        connected_clients.remove(websocket)

async def start_websocket():
    """Avvia il WebSocket Server."""
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/")
    await server.wait_closed()

def run_flask():
    """Avvia Flask in un thread separato per gestire richieste HTTP."""
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    try:
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
