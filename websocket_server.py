import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 8080))  # Porta assegnata da Render

async def handler(websocket, path):
    """Gestisce connessioni WebSocket e rifiuta richieste HTTP."""
    # Se la connessione non è WebSocket, chiudila subito
    if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
        print("⚠️ Richiesta HTTP ricevuta e ignorata")
        await websocket.close(code=1002)  # Chiudiamo la connessione pulita
        return

    print("✅ Nuova connessione WebSocket accettata!")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")  # Risponde con lo stesso messaggio
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
    try:
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
