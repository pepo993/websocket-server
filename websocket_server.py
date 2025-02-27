import asyncio
import json
import websockets
import os

PORT = int(os.getenv("PORT", 8080))  # Usa la porta assegnata da Render

connected_clients = set()
ultimo_stato_trasmesso = None  

async def notify_clients():
    """Invia aggiornamenti ai client WebSocket solo se lo stato cambia."""
    global ultimo_stato_trasmesso
    
    while True:
        if connected_clients:
            try:
                game_data = {"status": "partita in corso"}  # ⚠ Sostituisci con `load_game_data()`
                
                stato_attuale = {
                    "message": "Aggiornamento partita",
                    "data": game_data
                }
                
                if stato_attuale == ultimo_stato_trasmesso:
                    await asyncio.sleep(2)
                    continue  
                
                ultimo_stato_trasmesso = stato_attuale
                message = json.dumps(stato_attuale)
                
                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except Exception:
                        disconnected_clients.add(client)

                for client in disconnected_clients:
                    connected_clients.remove(client)

            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")

        await asyncio.sleep(2)


async def handler(websocket, path):
    """Gestisce connessioni WebSocket."""
    connected_clients.add(websocket)
    print(f"🔗 Nuovo client connesso! Totale: {len(connected_clients)}")

    try:
        async for _ in websocket:
            pass  
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale: {len(connected_clients)}")


async def start_server():
    """Avvia il WebSocket Server."""
    print(f"✅ Avviando WebSocket Server su porta {PORT}...")
    
    server = await websockets.serve(handler, "0.0.0.0", PORT)

    await asyncio.gather(server.wait_closed(), notify_clients())


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
