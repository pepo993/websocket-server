import asyncio
import websockets
import os
from aiohttp import web

PORT = int(os.getenv("PORT", 10000))  # Porta WebSocket
HTTP_PORT = 8080  # Porta HTTP per il health check di Render

connected_clients = set()

async def websocket_handler(websocket, path):
    """Gestisce connessioni WebSocket e filtra richieste HTTP non valide."""
    if path != "/ws":  # Blocca richieste HTTP che non sono WebSocket
        print(f"❌ Richiesta non WebSocket ricevuta: {path}. Chiudo la connessione.")
        await websocket.close()
        return

    print("🔗 Client connesso via WebSocket")
    connected_clients.add(websocket)

    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")  # Risponde con Echo
    except websockets.exceptions.ConnectionClosed:
        print("🔴 Client disconnesso")
    finally:
        connected_clients.remove(websocket)

async def start_websocket_server():
    """Avvia il WebSocket Server."""
    server = await websockets.serve(websocket_handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket attivo su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

async def health_check(request):
    """Server HTTP per il controllo di Render"""
    return web.Response(text="OK", status=200)

async def start_http_server():
    """Avvia un server HTTP per il controllo di salute."""
    app = web.Application()
    app.router.add_get("/", health_check)  # ✅ SOLO GET, niente HEAD
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    print(f"✅ Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}")

async def main():
    await asyncio.gather(start_websocket_server(), start_http_server())

if __name__ == "__main__":
    asyncio.run(main())
