import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 8080))  # 🔴 Usa la porta assegnata da Render

async def handler(websocket, path):
    """
    Gestisce solo connessioni WebSocket e rifiuta richieste HTTP.
    """
    try:
        # 🔴 Blocca connessioni che non sono WebSocket (Render sta mandando richieste HTTP)
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            print("❌ Connessione HTTP rifiutata (non è un WebSocket)")
            await websocket.close()
            return

        print("✅ Nuova connessione WebSocket")
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")

    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_server():
    """
    Avvia il server WebSocket e rifiuta richieste HTTP normali.
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

