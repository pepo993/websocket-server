import asyncio
import websockets
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
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
                
                # 📊 Crea lo stato attuale del gioco con tutti i dati
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],  # ✅ Lista completa dei numeri estratti
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data["players"].values()),
                        "jackpot": len(game_data["players"]) * 1,
                        "giocatori_attivi": len(game_data["players"]),
                        "vincitori": game_data.get("winners", {})  # ✅ Mostra i vincitori (se presenti)
                    },
                    "players": {
                        user_id: {
                            "cartelle": game_data["players"][user_id],  # ✅ Lista cartelle del giocatore
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


# 🔴 Usa la porta assegnata da Render
WS_PORT = int(os.getenv("PORT", 8080))  # Render fornisce automaticamente la porta
HTTP_PORT = 10001  # 🔴 Porta fissa per l'health check (deve essere diversa da WS_PORT)

async def handler(websocket, path):
    """
    Gestisce solo connessioni WebSocket e ignora richieste HTTP.
    """
    print("✅ Nuova connessione WebSocket accettata!")
    try:
        async for message in websocket:
            print(f"📩 Messaggio ricevuto: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")

async def start_websocket():
    """
    Avvia il server WebSocket sulla porta fornita da Render.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        WS_PORT
    )
    print(f"✅ WebSocket Server avviato su ws://0.0.0.0:{WS_PORT}/")

    await server.wait_closed()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Server HTTP per l'Health Check di Render.
    """
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"WebSocket Server Running")
        else:
            self.send_response(404)
            self.end_headers()

def start_http_server():
    """
    Avvia un piccolo server HTTP per l'Health Check di Render.
    """
    try:
        server = HTTPServer(("0.0.0.0", HTTP_PORT), HealthCheckHandler)
        print(f"🌍 Server HTTP avviato su http://0.0.0.0:{HTTP_PORT}/")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Errore nell'avvio del server HTTP: {e}")

if __name__ == "__main__":
    try:
        # Avvia il server HTTP per l'health check in un thread separato
        threading.Thread(target=start_http_server, daemon=True).start()
        
        # Avvia il WebSocket Server sulla porta fornita da Render
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
