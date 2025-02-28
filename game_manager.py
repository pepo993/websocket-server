import random
from transaction import send_payment, save_win
from game_logic import generate_bingo_card, check_winners, load_game_data, save_game_data
from bingo_bot import bot

# Dizionario per memorizzare le partite in corso
games = {}
TOTAL_NUMBERS = 90  # Totale numeri in gioco
COSTO_CARTELLA = 1  # Prezzo per ogni cartella acquistata

# Crea una nuova partita con ID univoco
def create_new_game():
    game_id = str(random.randint(1000, 9999))  # Genera un ID univoco per la partita
    games[game_id] = {
        "players": {},  # Traccia i giocatori e il numero di cartelle
        "jackpot": 0,  # Ammontare totale del jackpot
        "drawn_numbers": [],  # Lista dei numeri estratti
        "game_active": True  # Stato della partita
    }
    return game_id

# Avvia una nuova partita
def start_new_game(user_id):
    game_id = create_new_game()
    games[game_id]["players"][user_id] = []  # Aggiungi il giocatore senza cartelle iniziali
    return game_id

# Aggiorna il jackpot quando un giocatore acquista cartelle
def update_jackpot(game_id, num_cartelle):
    game_data = load_game_data()
    # Se il gioco non è attivo, non aggiornare il jackpot
    if not game_data.get("game_active", False):
        print(f"⚠️ Il gioco {game_id} non è attivo, impossibile aggiornare il jackpot.")
        return
    
    # Assicura che il jackpot esista nel game_data
    if "jackpot" not in game_data:
        game_data["jackpot"] = 0
    # Aggiorna il jackpot con il costo delle cartelle acquistate
    game_data["jackpot"] += num_cartelle * COSTO_CARTELLA
    # Salva il nuovo stato del gioco
    save_game_data(game_data)
    print(f"💰 Jackpot aggiornato: {game_data['jackpot']} TON per il gioco {game_id}.")


# Acquisto cartelle di gioco
def buy_ticket(user_id, game_id, num_cartelle=1):
    if not games.get(game_id) or not games[game_id]["game_active"]:
        return "❌ <b>Nessuna partita attiva.</b> Usa <code>/start_game</code> per avviarne una nuova."
    
    if user_id not in games[game_id]["players"]:
        games[game_id]["players"][user_id] = []
        
    games[game_id]["players"][user_id].extend([generate_bingo_card() for _ in range(num_cartelle)])
    update_jackpot(game_id, num_cartelle)
    
    return (f"✅ <b>Hai acquistato {num_cartelle} cartelle per la partita {game_id}.</b>\n"
            "🎰 <i>Buona fortuna!</i> 🍀\n"
            f"💰 <b>Jackpot attuale:</b> {games[game_id]['jackpot']} TON")


# Gestisce la fine del gioco e distribuisce il jackpot ai vincitori
async def handle_game_end(game_id):
    game_data = load_game_data()
    winners = check_winners(game_data)  # ✅ Ora restituisce {"Cinquina": [...], "Bingo": [...]}
    
    if winners["Bingo"] or winners["Cinquina"]:
        jackpot = game_data.get("jackpot", 0)
        num_bingo_winners = len(winners["Bingo"])
        num_cinquina_winners = len(winners["Cinquina"])
        bingo_prize = (jackpot * 0.9) / num_bingo_winners if num_bingo_winners > 0 else 0
        cinquina_prize = (jackpot * 0.1) / num_cinquina_winners if num_cinquina_winners > 0 else 0
        
        # 🏆 Notifica vincitori della Cinquina
        for winner in winners["Cinquina"]:
            success = send_payment(winner, cinquina_prize, "TON")
            if success:
                save_win(winner, game_id, "Cinquina", cinquina_prize)
                
        # 🎉 Notifica vincitori del Bingo
        for winner in winners["Bingo"]:
            success = send_payment(winner, bingo_prize, "TON")
            if success:
                save_win(winner, game_id, "Bingo", bingo_prize)
                
        game_data["game_active"] = False  # 🔴 Ferma il gioco dopo la vincita
        save_game_data(game_data)
        
    else:
        await bot.send_message(
            game_id,
            "❌ <b>Nessun vincitore in questa partita.</b>\n"
            "🎲 <i>Riprova nella prossima partita!</i>\n"
            "🎟️ <b>Acquista subito le tue cartelle con</b> <code>/buy N</code> e tenta la fortuna! 🍀"
        )
        
    games.pop(game_id)  # Rimuove la partita per liberare memoria
