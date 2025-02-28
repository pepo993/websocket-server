import asyncio
import json
import websockets
import os
import datetime
from game_logic import load_game_data

# Ottieni la porta dinamica assegnata da Railway
PORT = int(os.getenv("PORT", 8002))

connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

async def notify_clients():
    global ultimo_stato_trasmesso  
    while True:
        if connected_clients:
            try:
                game_data = load_game_data()

                if not game_data or "drawn_numbers" not in game_data:
                    print("Errore: Dati del gioco non validi.")
                    await asyncio.sleep(2)
                    continue  

                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data.get("players", {}).values()),
                        "jackpot": len(game_data.get("players", {})) * 1,
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "vincitori": game_data.get("winners", {})
                    },
                    "players": {
                        user_id: {"cartelle": game_data["players"][user_id]}
                        for user_id in game_data.get("players", {})
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
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)
                    except Exception as e:
                        print(f"Errore generico durante l'invio: {e}")
                        disconnected_clients.add(client)
                        
                for client in disconnected_clients:
                    connected_clients.remove(client)
                    
            except Exception as e:
                print(f"Errore generale in notify_clients: {e}")
        
        await asyncio.sleep(2)

async def handler(websocket, path):
    connected_clients.add(websocket)
    print(f"Nuovo client connesso! Totale: {len(connected_clients)}")
    try:
        async for message in websocket:
            print(f"Messaggio ricevuto: {message}")
            await websocket.send(json.dumps({"status": "ok", "message": "Connesso al WebSocket Server"}))
    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnesso normalmente.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Errore di connessione WebSocket: {e}")
    except Exception as e:
        print(f"Errore generale WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnesso! Totale attivi: {len(connected_clients)}")

async def start_server():
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"WebSocket Server avviato su ws://0.0.0.0:{PORT}/ws")
    await asyncio.gather(server.wait_closed(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"Errore nell'avvio del WebSocket Server: {e}")

