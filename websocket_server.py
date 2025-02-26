from aiohttp import web
import asyncio
import websockets
import os

PORT = int(os.getenv("PORT", 10000))  # WebSocket
HTTP_PORT = 8080  # Server HTTP per Render

async def handler(websocket, path):
    if path != "/ws":
        await websocket.close()
        return
    print("🔗 WebSocket Connesso")
    try:
        async for message in websocket:
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("🔴 Disconnessione WebSocket")

async def start_websocket_server():
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ WebSocket attivo su ws://0.0.0.0:{PORT}/ws")
    await server.wait_closed()

async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_http_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_head("/", health_check)  # Per richieste HEAD di Render
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    print(f"✅ Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}")

async def main():
    await asyncio.gather(start_websocket_server(), start_http_server())

if __name__ == "__main__":
    asyncio.run(main())
