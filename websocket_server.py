import asyncio
import json
import websockets
import os

PORT = int(os.getenv("PORT", 10000))  # Usa la porta di Render se disponibile

connected_clients = set()

async def handler(websocket, path):
    """Gestisce le connessioni WebSocket"""
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("🔴 Connessione chiusa")
    finally:
        connected_clients.remove(websocket)

async def start_server():
    """Avvia il WebSocket Server sulla porta fornita da Render"""
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())
