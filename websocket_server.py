import asyncio
import json
import websockets
import datetime
from multiprocessing import Process
import gunicorn.app.base
from flask import Flask

# Importa la logica del gioco
from game_logic import load_game_data   

app = Flask(__name__)

connected_clients = set()
ultimo_stato_trasmesso = None  # Memorizza l'ultimo stato inviato

@app.route('/')
def home():
    return "WebSocket Server is running!"


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
    """
    Gestisce le connessioni WebSocket con la WebApp.
    """
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "Sconosciuto"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"🔗 Nuovo client connesso da {client_ip} - {timestamp}")

    try:
        async for _ in websocket:
            pass
    except Exception as e:
        print(f"⚠️ Errore WebSocket: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Client disconnesso! Totale client attivi: {len(connected_clients)}")


async def start_websocket():
    """
    Avvia il server WebSocket con gestione avanzata delle connessioni.
    """
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        8002,
        ping_interval=5,  
        ping_timeout=None
    )
    print("✅ WebSocket Server avviato su ws://0.0.0.0:8002")

    await asyncio.gather(server.wait_closed(), notify_clients())


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """
    Configura Gunicorn per eseguire il server Flask in modalità produzione.
    """
    def __init__(self, app, options=None):
        self.application = app
        self.options = options or {}
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application


def start_gunicorn():
    """
    Avvia Gunicorn per servire le richieste HTTP.
    """
    options = {
        'bind': '0.0.0.0:10000',
        'workers': 2
    }
    StandaloneApplication(app, options).run()


if __name__ == "__main__":
    try:
        # Avvia il server Flask con Gunicorn in un processo separato
        flask_process = Process(target=start_gunicorn)
        flask_process.start()
        
        # Avvia il WebSocket Server
        asyncio.run(start_websocket())
    except Exception as e:
        print(f"❌ Errore nell'avvio del WebSocket Server: {e}")
