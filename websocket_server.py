import os
import asyncio
import json
import websockets

async def handler(websocket, path):
    """
    Gestisce solo connessioni WebSocket valide su `/ws`.
    """
    if path != "/ws":
        print(f"❌ Connessione rifiutata: percorso non valido {path}")
        await websocket.close()
        return

    print("✅ Nuovo client WebSocket connesso!")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(json.dumps({"response": "Messaggio ricevuto"}))
    except websockets.ConnectionClosed:
        print("🔴 Connessione WebSocket chiusa")
    finally:
        print("🔌 Client disconnesso")

async def main():
    """
    Avvia il WebSocket Server su Render con porta dinamica.
    """
    PORT = int(os.environ.get("PORT", 10000))

    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT,
        subprotocols=["binary"]
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

