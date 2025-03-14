import os
import json
import asyncio
import websockets
from aiohttp import web
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal
from models import Game, Ticket, User
from config import COSTO_CARTELLA
import traceback  # 🔥 Per log più dettagliati
import config 

# 📌 Assicura che INFO vada su stdout
import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout  
)

# 📌 Imposta il logging dettagliato
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Porta assegnata per Railway (default: 8002)
PORT = int(os.getenv("PORT", 8002))

# 📌 Set di client connessi
connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

# 📌 Funzione per caricare lo stato del gioco dal database
async def load_game_state():
    async with SessionLocal() as db:
        try:
            logging.info("🔄 Caricamento stato del gioco dal database...")

            result = await db.execute(select(Game).filter(Game.active == True))
            game = result.scalars().first()

            if not game:
                logging.warning("⚠️ Nessuna partita attiva trovata.")
                return {"drawn_numbers": [], "players": {}, "winners": {}, "userInfo": {}}

            logging.info(f"🎮 Partita attiva trovata: {game.game_id}")

            # 🔍 Controlla se tutti i numeri sono stati estratti
            drawn_numbers = list(map(int, game.drawn_numbers.split(","))) if game.drawn_numbers else []
            logging.info(f"🔢 Numeri estratti: {len(drawn_numbers)} su 90")

            # 🔹 Recupera i biglietti
            try:
                result = await db.execute(select(Ticket).filter(Ticket.game_id == game.game_id))
                tickets = result.scalars().all()
                logging.info(f"🎟️ Biglietti trovati: {len(tickets)}")
            except Exception as e:
                logging.error(f"❌ Errore nel recupero dei ticket: {e}")
                return {"drawn_numbers": drawn_numbers, "players": {}, "winners": {}, "userInfo": {}}

            players = {}
            # ✅ Recuperiamo tutti gli utenti in UNA SOLA query
            user_ids = [ticket.user_id for ticket in tickets]
            user_info = {}
            if user_ids:
                user_results = await db.execute(select(User.telegram_id, User.username, User.first_name).where(User.telegram_id.in_(user_ids)))
                users = {user.telegram_id: {"username": user.username, "first_name": user.first_name} for user in user_results}
                user_info = users  # ✅ Assegniamo direttamente i dati recuperati

            for ticket in tickets:
                if ticket.user_id not in players:
                    players[ticket.user_id] = {"cartelle": []}
                
                try:
                    players[ticket.user_id]["cartelle"].append(json.loads(ticket.numbers))
                except json.JSONDecodeError:
                    logging.error(f"❌ Errore nel parsing JSON per il ticket di {ticket.user_id}")

                if user:
                    user_info[ticket.user_id] = {
                        "username": user.username if user.username else None,
                        "first_name": user.first_name if user.first_name else None
                    }

            logging.info(f"👥 Giocatori trovati: {len(players)}")

            return {
                "drawn_numbers": drawn_numbers,
                "players": players,
                "winners": {},
                "userInfo": user_info  # ✅ Aggiunto userInfo alla risposta WebSocket
            }
        except Exception as e:
            logging.error(f"❌ Errore nel caricamento dello stato del gioco: {e}")
            return {"drawn_numbers": [], "players": {}, "winners": {}, "userInfo": {}}


# 📌 Funzione per salvare lo stato del gioco
async def save_game_state(state):
    async with SessionLocal() as db:
        try:
            logging.info("💾 Tentativo di salvataggio dello stato del gioco...")

            result = await db.execute(select(Game).filter(Game.active == True))
            game = result.scalars().first()

            if game:
                game.drawn_numbers = ",".join(map(str, state["drawn_numbers"]))
                await db.commit()
                logging.info("✅ Stato del gioco aggiornato nel database.")
            else:
                logging.warning("⚠️ Nessuna partita attiva trovata per il salvataggio.")
        except Exception as e:
            logging.error(f"❌ Errore nel salvataggio dello stato del gioco: {e}")
            logging.error(traceback.format_exc())  # 🔥 Stack trace completo
            await db.rollback()

# 📌 Gestione delle connessioni WebSocket
import json
import logging
import websockets

connected_clients = set()

async def handler(websocket):
    """Gestisce la connessione WebSocket dei client e trasmette gli aggiornamenti."""
    connected_clients.add(websocket)
    logging.info(f"✅ Nuovo client connesso! Totale: {len(connected_clients)} - {websocket.remote_address}")

    try:
        async for message in websocket:  # 🔹 Nessun timeout, connessione aperta finché il client è connesso
            logging.info(f"📥 Messaggio ricevuto: {message}")

            try:
                game_state = json.loads(message)

                # 🔄 Salva lo stato del gioco se contiene numeri estratti
                if "drawn_numbers" in game_state:
                    await save_game_state(game_state)
                    logging.info("📌 Stato del gioco aggiornato con nuovi numeri estratti.")

                    # 📢 Trasmette l'aggiornamento a tutti i client connessi
                    broadcast_message = json.dumps(game_state)

                    # 🔄 Invia solo ai client ancora attivi
                    active_clients = {client for client in connected_clients if not client.closed}
                    for client in active_clients:
                        await client.send(broadcast_message)

                    # 🧹 Aggiorna la lista dei client connessi
                    connected_clients.clear()
                    connected_clients.update(active_clients)

            except json.JSONDecodeError:
                logging.error("❌ Errore: Messaggio non è un JSON valido.")
                await websocket.send(json.dumps({"error": "Messaggio JSON non valido"}))

    except websockets.exceptions.ConnectionClosed:
        logging.warning(f"⚠️ Il client {websocket.remote_address} si è disconnesso.")

    finally:
        # Rimuove il client dalla lista solo quando si disconnette
        connected_clients.discard(websocket)
        logging.info(f"❌ Client rimosso dalla lista. Totale attivi: {len(connected_clients)}")


# 📌 Funzione per notificare i client attivi
async def notify_clients():
    global ultimo_stato_trasmesso

    while True:
        if connected_clients:
            try:
                game_data = await load_game_state()
                await asyncio.sleep(1.5)

                if not game_data or "drawn_numbers" not in game_data:
                    logging.error("❌ Dati di gioco non validi.")
                    await asyncio.sleep(5)
                    continue  

                # 📌 Costruisce lo stato attuale del gioco
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p["cartelle"]) for p in game_data.get("players", {}).values()),
                        "jackpot": sum(len(p["cartelle"]) for p in game_data.get("players", {}).values()) * COSTO_CARTELLA,
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "vincitori": game_data.get("winners", {}),
                    },
                    "players": game_data["players"]
                }

                # 📤 Invia solo se lo stato è cambiato
                if stato_attuale != ultimo_stato_trasmesso:
                    ultimo_stato_trasmesso = stato_attuale
                    message = json.dumps(stato_attuale)

                    disconnected_clients = set()
                    for client in connected_clients:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(client)

                    for client in disconnected_clients:
                        connected_clients.discard(client)

                    logging.info(f"📤 Dati inviati ai client WebSocket: {message}")

            except Exception as e:
                logging.error(f"❌ Errore in notify_clients: {e}")

        await asyncio.sleep(2)

# 📌 Health Check per Railway
async def health_check(request):
    """Testa la connessione al database e il numero di client attivi."""
    async with SessionLocal() as db:
        try:
            await db.execute(select(1))  # Query di test
            db_status = "🟢 Database OK"
        except:
            db_status = "🔴 Errore Database"

    ws_status = f"🟢 Client attivi: {len(connected_clients)}" if connected_clients else "🟡 Nessun client connesso"

    return web.Response(text=f"{db_status}\n{ws_status}", status=200)


# 📌 Configura il server HTTP per l'health check
app = web.Application()
app.router.add_get('/health', health_check)

# 📌 Avvio del WebSocket Server
async def start_server():
    websocket_server = await websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None, ping_timeout=None)
    logging.info(f"🚀 WebSocket Server avviato su ws://0.0.0.0:{PORT}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("✅ Health check attivo su http://0.0.0.0:8080/health")

    await asyncio.gather(websocket_server.wait_closed(), notify_clients())

# 📌 Avvio del server
if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except Exception as e:
        logging.error(f"❌ Errore nell'avvio del WebSocket Server: {e}")
