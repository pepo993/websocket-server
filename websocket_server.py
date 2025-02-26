import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 8002))

async def handler(websocket, path):
    """
    Gestisce le connessioni WebSocket e rifiuta richieste HTTP normali.
    """
    try:
        # 🔴 Rifiuta connessioni che non sono WebSocket (ad esempio richieste HEAD di Render)
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            print("❌ Connessione HTTP rifiutata (non è un WebSocket)")
            await websocket.close()
            return

        print("✅ Nuova connessione WebSocket")
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")  # 🔵 Risponde con un messaggio di test

    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_server():
    """
    Avvia il server WebSocket e rifiuta richieste HTTP normali.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")

    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
