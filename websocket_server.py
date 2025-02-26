import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 8080))  # 🔴 Render assegna automaticamente la porta

async def handler(websocket, path):
    print("✅ Nuova connessione WebSocket")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """
    Avvia il WebSocket Server.
    """
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
