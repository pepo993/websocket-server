import os
import json
import asyncio
import websockets
from aiohttp import web
from config import COSTO_CARTELLA

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal
from models import Game, Ticket

# 📌 Porta assegnata per Railway (default: 8002)
PORT = int(os.getenv("PORT", 8002))

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
    """ Gestisce le connessioni WebSocket """
    connected_clients.add(websocket)
    print(f"✅ Nuovo client connesso! Totale: {len(connected_clients)} - {websocket.remote_address}")

    try:
        async for message in websocket:
            print(f"📥 Messaggio ricevuto: {message}")

            try:
                game_state = json.loads(message)
                if "drawn_numbers" in game_state:
                    save_game_state(game_state)
                    print("📌 Stato del gioco aggiornato con nuovi numeri estratti.")

                    # 📢 Invia l'aggiornamento a tutti i client connessi
                    broadcast_message = json.dumps(game_state)
                    for client in list(connected_clients):  # Itera su una copia per evitare problemi di rimozione
                        try:
                            await client.send(broadcast_message)
                        except websockets.exceptions.ConnectionClosed:
                            connected_clients.discard(client)
                            print(f"❌ Client disconnesso rimosso. Totale attivi: {len(connected_clients)}")

            except json.JSONDecodeError:
                print("❌ Errore: Messaggio non è un JSON valido.")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"⚠️ Client disconnesso normalmente: {e}")

    finally:
        connected_clients.discard(websocket)
        print(f"❌ Client rimosso dalla lista. Totale attivi: {len(connected_clients)}")

# 📌 Funzione per notificare i client attivi
async def notify_clients():
    """ Invia aggiornamenti solo se lo stato è cambiato """
    global ultimo_stato_trasmesso

    while True:
        if connected_clients:
            try:
                game_data = load_game_state()

                if not game_data or "drawn_numbers" not in game_data:
                    print("❌ Dati di gioco non validi.")
                    await asyncio.sleep(3)
                    continue  

                # ⏳ Imposta il tempo della prossima partita se non esiste
                import time
                next_game_time = game_data.get("next_game_time", int((time.time() + 120) * 1000))

                # 📌 Costruisce lo stato attuale del gioco
                stato_attuale = {
                    "numero_estratto": game_data["drawn_numbers"][-1] if game_data["drawn_numbers"] else None,
                    "numeri_estratti": game_data["drawn_numbers"],
                    "game_status": {
                        "cartelle_vendute": sum(len(p) for p in game_data.get("players", {}).values()),
                        "jackpot": sum(len(p) for p in game_data.get("players", {}).values()) * COSTO_CARTELLA,
                        "giocatori_attivi": len(game_data.get("players", {})),
                        "vincitori": game_data.get("winners", {}),
                        "next_game_time": next_game_time,
                    },
                    "players": {
                        user_id: {"cartelle": game_data["players"][user_id]}
                        for user_id in game_data.get("players", {})
                    }
                }

                # 📤 Invia solo se lo stato è cambiato
                if stato_attuale != ultimo_stato_trasmesso:
                    ultimo_stato_trasmesso = stato_attuale  # Aggiorna lo stato memorizzato
                    message = json.dumps(stato_attuale)

                    for client in list(connected_clients):  # Itera su una copia per sicurezza
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            connected_clients.discard(client)
                            print(f"❌ Client disconnesso rimosso. Totale attivi: {len(connected_clients)}")

                    print(f"📤 Dati inviati ai client WebSocket: {message}")

            except Exception as e:
                print(f"❌ Errore in notify_clients: {e}")

        await asyncio.sleep(2)  # Mantiene un intervallo di aggiornamento di 2s

# 📌 Health Check per Railway
async def health_check(request):
    return web.Response(text="OK", status=200)

# Configura il server HTTP per l'health check
app = web.Application()
app.router.add_get('/health', health_check)

# 📌 Avvio del WebSocket Server
async def start_server():
    async with websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None, ping_timeout=None) as websocket_server:
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

