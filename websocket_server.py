import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 8002))  # 🔴 Usa la porta assegnata da Render

async def handler(websocket, path):
    print("✅ Nuova connessione WebSocket")
    async for message in websocket:
        print(f"📩 Messaggio ricevuto: {message}")
        await websocket.send(f"Echo: {message}")

async def start_server():
    """
    Avvia il WebSocket su Render con supporto `wss://`
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",  # 🔴 Accetta connessioni pubbliche
        PORT
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")

    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
