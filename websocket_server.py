import asyncio
import json
import websockets
import os
import datetime
from flask import Flask
from threading import Thread
from game_logic import load_game_data

# Mini server Flask per rispondere a richieste HTTP
app = Flask(__name__)

@app.route("/")
def home():
    return "WebSocket Server is running!", 200

@app.route("/health")
def health_check():
    return "OK", 200

def run_flask():
    """Avvia Flask in un thread separato."""
    flask_port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=flask_port)

# WebSocket Server
connected_clients = set()

async def handler(websocket, path):
    """Gestisce le connessioni WebSocket."""
    try:
        connected_clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "Sconosciuto"
        print(f"🔗 Nuovo client connesso da {client_ip}")

        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"⚠️ Errore di connessione WebSocket: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")

async def start_websocket():
    """Avvia il WebSocket Server."""
    try:
        WS_PORT = int(os.environ.get("WS_PORT", 8002))  # Porta WebSocket assegnata da Render
        server = await websockets.serve(handler, "0.0.0.0", WS_PORT)
        print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{WS_PORT}/ws")
        await server.wait_closed()
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")

if __name__ == "__main__":
    # Avvia Flask in un thread separato
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Avvia il WebSocket server
    asyncio.run(start_websocket())

