import asyncio
import json
import websockets
import datetime
from game_logic import load_game_data

connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

async def notify_clients():
    """
    Invia aggiornamenti ai client WebSocket solo se ci sono nuove informazioni.
    """
    global ultimo_stato_trasmesso  
    
    while True:
        if connected_clients:
            try:
                game_data = load_game_data()
                
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data["players"].values()),
                        "jackpot": len(game_data["players"]) * 1,
                        "giocatori_attivi": len(game_data["players"]),
                        "vincitori": game_data.get("winners", {})
                    },
                    "players": {
                        user_id: {
                            "cartelle": game_data["players"][user_id]
                        }
                        for user_id in game_data["players"]
                    }
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
                    except Exception as e:
                        print(f"⚠️ Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)
                        
                for client in disconnected_clients:
                    connected_clients.remove(client)
                    
            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")
                
        await asyncio.sleep(2)


async def handler(websocket, path):
    """Gestisce connessioni WebSocket con logging dettagliato."""
    try:
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            print("⚠️ Richiesta HTTP ricevuta e ignorata")
            return

        print(f"✅ Nuova connessione WebSocket da {websocket.remote_address}")

        connected_clients.add(websocket)
        
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"🔴 Connessione chiusa: codice {e.code}, motivo: {e.reason}")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso. Totale attivi: {len(connected_clients)}")



async def start_server():
    """
    Avvia il server WebSocket con gestione avanzata delle connessioni.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        8080,
        ping_interval=5,  
        ping_timeout=None
    )
    print("✅ WebSocket Server avviato su ws://0.0.0.0:8080")

    await asyncio.gather(server.wait_closed(), notify_clients())


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
