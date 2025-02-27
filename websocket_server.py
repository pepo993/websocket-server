import asyncio
import os
import threading
import websockets
from flask import Flask

PORT = int(os.getenv("PORT", 10000))  # Porta WebSocket
HTTP_PORT = 5000  # Porta HTTP per Render

connected_clients = set()

# ✅ Mini server Flask per Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ WebSocket Server is Running!", 200  # Render riconosce il servizio HTTP

async def websocket_handler(websocket, path):
    """Gestisce le connessioni WebSocket"""
    connected_clients.add(websocket)
    print("✅ Client connesso!")

    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")

    except websockets.exceptions.ConnectionClosed:
        print("🔴 Connessione chiusa")

    finally:
        connected_clients.remove(websocket)

async def start_websocket():
    """Avvia il WebSocket Server"""
    server = await websockets.serve(websocket_handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/")
    await server.wait_closed()

def run_flask():
    """Avvia Flask per gestire richieste HTTP su Render"""
    app.run(host="0.0.0.0", port=HTTP_PORT)

if __name__ == "__main__":
    # Avvia il server HTTP in un thread separato
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Avvia il WebSocket Server
    asyncio.run(start_websocket())
