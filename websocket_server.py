import asyncio
import websockets
from aiohttp import web

# Health check per Render
async def health_check(request):
    return web.Response(text="OK", status=200)

# Server HTTP per rispondere alle richieste di Render
app = web.Application()
app.router.add_get('/health', health_check)

# Gestione delle connessioni WebSocket
connected_clients = set()

async def websocket_handler(websocket, path):
    # Aggiungi il client alla lista delle connessioni attive
    connected_clients.add(websocket)
    print(f"Nuova connessione WebSocket: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")  # Risponde con un echo
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connessione chiusa: {e}")
    finally:
        # Rimuovi il client disconnesso
        connected_clients.remove(websocket)
        print("Client disconnesso")

async def main():
    # Avvia il server WebSocket sulla porta 8000
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8000)
    print("Server WebSocket in ascolto sulla porta 8000")
    
    # Avvia il server HTTP per il health check sulla porta 8080
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Health check attivo sulla porta 8080")

    await asyncio.Future()  # Mantieni il server attivo

if __name__ == "__main__":
    asyncio.run(main())

    # Flask verrà eseguito con Gunicorn, quindi non avviamo direttamente app.run()
