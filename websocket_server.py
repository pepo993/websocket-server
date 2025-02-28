import asyncio
import os
import websockets
from aiohttp import web

# Recupera la porta assegnata da Render
PORT = int(os.getenv("PORT", 8080))  # Render assegna dinamicamente la porta

# Health check per Render
async def health_check(request):
    return web.Response(text="OK", status=200)

# Server HTTP per rispondere alle richieste di Render
app = web.Application()
app.router.add_get('/health', health_check)

# Gestione delle connessioni WebSocket
connected_clients = set()

async def websocket_handler(websocket):
    connected_clients.add(websocket)
    print(f"Nuova connessione WebSocket: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")  # Risponde con un echo
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connessione chiusa: {e}")
    finally:
        connected_clients.remove(websocket)
        print("Client disconnesso")

async def main():
    # Avvia il server WebSocket sulla porta assegnata da Render
    server = await websockets.serve(websocket_handler, "0.0.0.0", PORT)
    print(f"Server WebSocket in ascolto sulla porta {PORT}")

    # Avvia il server HTTP per il health check
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Health check attivo sulla porta 8080")

    await asyncio.Future()  # Mantieni il server attivo

if __name__ == "__main__":
    asyncio.run(main())

    # Flask verrà eseguito con Gunicorn, quindi non avviamo direttamente app.run()
