import os
import json
import asyncio
import websockets
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal
from models import Game, Ticket, User
import logging

# 📌 Configura il logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Porta assegnata per Railway (default: 8002)
PORT = int(os.getenv("PORT", 8002))

# 📌 Set di client connessi
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato per evitare duplicati

# 📌 Funzione per caricare lo stato del gioco dal database
async def load_game_state():
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(Game).filter(Game.active == True))
            game = result.scalars().first()
            
            if not game:
                logging.warning("⚠️ Nessuna partita attiva trovata nel database.")
                return {"drawn_numbers": [], "players": {}, "winners": {}}

            # Recupera i numeri estratti
            drawn_numbers = list(map(int, game.drawn_numbers.split(","))) if game.drawn_numbers else []

            # Recupera i giocatori e le cartelle
            result = await db.execute(select(Ticket).filter(Ticket.game_id == game.game_id))
            tickets = result.scalars().all()

            players = {}
            for ticket in tickets:
                if ticket.user_id not in players:
                    players[ticket.user_id] = {"cartelle": []}
                players[ticket.user_id]["cartelle"].append(list(map(int, ticket.numbers.split(","))))

            return {
                "drawn_numbers": drawn_numbers,
                "players": players,
                "winners": {}  # I vincitori saranno aggiornati separatamente
            }
        except Exception as e:
            logging.error(f"❌ Errore nel caricamento dello stato del gioco: {e}")
            return {"drawn_numbers": [], "players": {}, "winners": {}}

# 📌 Funzione per salvare lo stato del gioco nel database
async def save_game_state(state):
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(Game).filter(Game.active == True))
            game = result.scalars().first()
            
            if game:
                game.drawn_numbers = ",".join(map(str, state["drawn_numbers"]))
                await db.commit()
                logging.info("✅ Stato del gioco aggiornato nel database.")
        except Exception as e:
            logging.error(f"❌ Errore nel salvataggio dello stato del gioco: {e}")

# 📌 Gestione delle connessioni WebSocket
async def handler(websocket):
    """ Gestisce le connessioni WebSocket dei client """
    connected_clients.add(websocket)
    logging.info(f"✅ Nuovo client connesso! Totale: {len(connected_clients)}")

    try:
        async for message in websocket:
            logging.info(f"📥 Messaggio ricevuto: {message}")

            try:
                game_state = json.loads(message)

                if "drawn_numbers" in game_state:
                    await save_game_state(game_state)  # ✅ Salva lo stato nel database

                    # 📢 Invia l'aggiornamento a tutti i client connessi
                    broadcast_message = json.dumps(game_state)
                    disconnected_clients = set()

                    for client in connected_clients:
                        try:
                            await client.send(broadcast_message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(client)

                    # Rimuove i client disconnessi
                    for client in disconnected_clients:
                        connected_clients.discard(client)
                        logging.info(f"❌ Client disconnesso rimosso. Totale attivi: {len(connected_clients)}")

            except json.JSONDecodeError:
                logging.error("❌ Errore: Messaggio non è un JSON valido.")

    except websockets.exceptions.ConnectionClosed:
        logging.warning("⚠️ Client disconnesso normalmente.")
    finally:
        if websocket in connected_clients:
            connected_clients.discard(websocket)
            logging.info(f"❌ Client rimosso dalla lista. Totale attivi: {len(connected_clients)}")

# 📌 Funzione per inviare aggiornamenti ai client
async def notify_clients():
    """ Invia aggiornamenti ai client WebSocket solo se lo stato è cambiato """
    global ultimo_stato_trasmesso

    while True:
        if connected_clients:
            try:
                game_data = await load_game_state()
                await asyncio.sleep(1.5)  # ✅ Evita di inviare troppi aggiornamenti

                if not game_data or "drawn_numbers" not in game_data:
                    logging.error("❌ Dati di gioco non validi.")
                    await asyncio.sleep(3)
                    continue  

                # 📌 Costruisce lo stato attuale del gioco
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data.get("drawn_numbers") else 0,
                    "numeri_estratti": game_data.get("drawn_numbers", []),
                    "game_status": {
                        "cartelle_vendute": sum(len(p["cartelle"]) for p in game_data.get("players", {}).values()),
                        "jackpot": sum(len(p["cartelle"]) for p in game_data.get("players", {}).values()) * 0.2, # Costo cartella 0.2 TON
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "winners": game_data.get("winners", {}),
                    },
                    "players": game_data.get("players", {})
                }

                # 📌 Evita di inviare aggiornamenti duplicati
                if stato_attuale == ultimo_stato_trasmesso:
                    await asyncio.sleep(3)
                    continue  
                    
                # ✅ Aggiorniamo lo stato trasmesso solo se è cambiato
                ultimo_stato_trasmesso = json.loads(json.dumps(stato_attuale))  # Deep copy
                message = json.dumps(stato_attuale)

                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        logging.warning("⚠️ Errore WebSocket durante l'invio.")
                        disconnected_clients.add(client)

                # 📌 Rimuove i client disconnessi
                for client in disconnected_clients:
                    connected_clients.discard(client)
                    logging.info(f"❌ Client disconnesso rimosso. Totale attivi: {len(connected_clients)}")

            except Exception as e:
                logging.error(f"❌ Errore in notify_clients: {e}")

        await asyncio.sleep(2)  # Mantiene un intervallo di aggiornamento di 2s


# 📌 Health Check per Railway
async def health_check(request):
    return web.Response(text="OK", status=200)

# Configura il server HTTP per l'health check
app = web.Application()
app.router.add_get('/health', health_check)

# 📌 Avvio del WebSocket Server
async def start_server():
    websocket_server = await websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None, ping_timeout=None)

    print(f"🚀 WebSocket Server avviato su ws://0.0.0.0:{PORT}")

    # Avvia il server HTTP per l'health check
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ Health check attivo su http://0.0.0.0:8080/health")

    await asyncio.gather(websocket_server.wait_closed(), notify_clients())

# 📌 Avvio del server
if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")

