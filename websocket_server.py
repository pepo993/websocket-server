import asyncio
import json
import websockets
import os
import datetime

from game_logic import load_game_data

connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

# 🔴 Usa la porta assegnata da Render
WS_PORT = int(os.getenv("PORT", 8080))

async def handler(websocket, path):
    """
    Gestisce connessioni WebSocket e rifiuta richieste HTTP normali.
    """
    try:
        # Verifica se la connessione è WebSocket
        if "Upgrade" not in websocket.request_headers or websocket.request_headers["Upgrade"].lower() != "websocket":
            print("⚠️ Richiesta HTTP ricevuta (non WebSocket) → Chiusura connessione")
            await websocket.close(code=1002)  # 🔴 Chiude connessioni non WebSocket
            return

        print("✅ Nuova connessione WebSocket accettata!")
        connected_clients.add(websocket)

        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")

    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")

async def notify_clients():
    """
    Invia aggiornamenti ai client WebSocket solo se ci sono nuove informazioni.
    """
    global ultimo_stato_trasmesso  
    while True:
        if connected_clients:
            try:
                game_data = load_game_data()

                # 📊 Stato attuale del gioco
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data["players"].values()),
                        "jackpot": len(game_data["players"]) * 1,
                        "giocatori_attivi": len(game_data["players"]),
                        "vincitori": game_data.get("winners", {})
                    },
                    "players": {user_id: {"cartelle": game_data["players"][user_id]} for user_id in game_data["players"]}
                }

                # 🔄 Se lo stato non è cambiato, non inviare nulla
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

                # Rimuove i client disconnessi
                for client in disconnected_clients:
                    connected_clients.remove(client)

            except Exception as e:
                print(f"❌ Errore in notify_clients: {e}")

        await asyncio.sleep(2)  # Mantiene aggiornamenti costanti

async def start_server():
    """
    Avvia il server WebSocket su Render.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        WS_PORT
    )
    print(f"✅ WebSocket Server avviato su wss://websocket-server-5muq.onrender.com/ws")
    
    # Avvia `notify_clients()` in parallelo
    await asyncio.gather(server.wait_closed(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
