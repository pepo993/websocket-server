import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 8080))  # Porta assegnata da Render

async def handler(websocket, path):
    """Gestisce connessioni WebSocket e risponde con un semplice echo."""
    print("✅ Nuova connessione WebSocket!")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")  # Risponde con il messaggio ricevuto
    except websockets.exceptions.ConnectionClosed:
        print("🔴 Connessione chiusa")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """Avvia il WebSocket Server sulla porta assegnata da Render."""
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_websocket())
