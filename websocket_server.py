import asyncio
import json
import websockets
import datetime
from game_logic import load_game_data
import os

PORT = int(os.getenv("PORT", 8002))  # Usa la porta assegnata da Render

connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

async def reject_http_requests(path, request_headers):
    """
    Rifiuta le richieste HTTP normali (HEAD, GET senza WebSocket).
    Render usa HEAD per i controlli di salute, quindi le ignoriamo.
    """
    if "Upgrade" not in request_headers or request_headers["Upgrade"].lower() != "websocket":
        return 400, [], b"WebSocket required\n"

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
                    "players": {
                        user_id: {
                            "cartelle": game_data["players"][user_id],
                        }
                        for user_id in game_data["players"]
                    }
                }
                
                # 🔄 Se lo stato non è cambiato, non inviare nulla
                if stato_attuale == ultimo_stato_trasmesso:
                    await asyncio.sleep(2)
                    continue  
                
                ultimo_stato_trasmesso = stato_attuale
                message = json.dumps(stato_attuale)
                
                # 🚀 Invia aggiornamenti ai client WebSocket
                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except Exception as e:
                        print(f"⚠️ Errore WebSocket durante l'invio: {e}")
                        disconnected_clients.add(client)
                        
                # Rimuove i client disconnessi
                for client in disconnected_clients:
                    connected_clients.remove(client)
                    
            except Exception as e:
                print(f"❌ Errore generale in notify_clients: {e}")
                
        await asyncio.sleep(2)  # Mantiene aggiornamenti costanti

async def handler(websocket, path):
    """
    Gestisce le connessioni WebSocket con la WebApp.
    """
    connected_clients.add(websocket)
    
    # 📍 Ottieni dettagli sulla connessione
    client_ip = websocket.remote_address[0] if websocket.remote_address else "Sconosciuto"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 📊 Stato della partita al momento della connessione
    game_data = load_game_data()
    numero_estratti = len(game_data["drawn_numbers"])
    giocatori_attivi = len(game_data["players"])
    jackpot = game_data.get("jackpot", 0)
    cartelle_vendute = sum(len(cartelle) for cartelle in game_data["players"].values())
    
    # 🔗 Log dettagliato della connessione
    print(f"""
🔗 **Nuovo client connesso!**
📍 **IP:** {client_ip}
⏳ **Timestamp:** {timestamp}
👥 **Client totali connessi:** {len(connected_clients)}

📊 **Stato della partita:**
🎰 **Numeri estratti:** {numero_estratti}/90
🎟️ **Cartelle vendute:** {cartelle_vendute}
👥 **Giocatori attivi:** {giocatori_attivi}
💰 **Jackpot:** {jackpot} TON
""")

    try:
        async for _ in websocket:
            pass  # Mantiene la connessione attiva
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")

async def start_server():
    """
    Avvia il server WebSocket con gestione avanzata delle connessioni.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT,
        process_request=reject_http_requests,  # 🔥 Blocca richieste HEAD/GET normali
        ping_interval=5,  # Mantiene le connessioni attive ogni 5 secondi
        ping_timeout=None
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{PORT}")

    # Avvia `notify_clients()` in parallelo
    await asyncio.gather(server.wait_closed(), notify_clients())

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
