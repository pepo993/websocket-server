import random
import json
import os

# Percorso del file per salvare lo stato del gioco
game_data_file = "data/game_data.json"

# Funzione per caricare lo stato del gioco
def load_game_data():
    if not os.path.exists(game_data_file):
        print("⚠️ Il file game_data.json non esiste, creando uno nuovo...")
        save_game_data({"players": {}, "drawn_numbers": [], "game_active": False})
        
    try:
        with open(game_data_file, "r") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"❌ Errore nel file game_data.json: {e}")
        save_game_data({"players": {}, "drawn_numbers": [], "game_active": False})
        return {"players": {}, "drawn_numbers": [], "game_active": False}

# Funzione per salvare lo stato del gioco
def save_game_data(data):
    with open(game_data_file, "w") as file:
        json.dump(data, file, indent=4)

# Funzione per avviare una nuova partita

def start_game():
    game_data = load_game_data()
    
    if game_data["players"] or "next_game_players" in game_data:
        game_data["drawn_numbers"] = []
        game_data["game_active"] = True
        
        # 🔄 Trasferisce i giocatori della prossima partita a quella attuale
        if "next_game_players" in game_data and game_data["next_game_players"]:
            print(f"🔄 Trasferimento giocatori alla nuova partita: {game_data['next_game_players']}")  # Debug
            game_data["players"] = game_data["next_game_players"]
            game_data["next_game_players"] = {}  # Resetta la lista
        
        save_game_data(game_data)
        return "🎲 Il Bingo è iniziato! I numeri verranno estratti automaticamente."
    
    return "⚠️ Nessun giocatore registrato! Acquista almeno una cartella con /buy."


# Funzione per acquistare una cartella di gioco
def buy_ticket(user_id, num_cartelle=1):
    game_data = load_game_data()
    
    max_cartelle = 24  # Numero massimo di cartelle acquistabili
    
    if game_data["game_active"]:
        if "next_game_players" not in game_data:
            game_data["next_game_players"] = {}
            
        if user_id not in game_data["next_game_players"]:
            game_data["next_game_players"][user_id] = []
        
        # 📌 🔴 Debug: Controlla se le cartelle vengono salvate correttamente
        print(f"📜 Debug: {user_id} sta acquistando {num_cartelle} cartelle per la prossima partita.")
        
        if len(game_data["next_game_players"][user_id]) + num_cartelle > max_cartelle:
            return f"❌ Puoi acquistare al massimo {max_cartelle} cartelle per la prossima partita."
        
        nuove_cartelle = [generate_bingo_card() for _ in range(num_cartelle)]
        game_data["next_game_players"][user_id].extend(nuove_cartelle)
        
        save_game_data(game_data)
        
        return f"⚠️ La partita è già iniziata! Le tue {num_cartelle} cartelle verranno utilizzate nella prossima partita."
    
    # Se il gioco non è attivo, il giocatore può acquistare cartelle normalmente
    if user_id not in game_data["players"]:
        game_data["players"][user_id] = []
        
    # Verifica che l'utente non superi il massimo di cartelle per la partita attuale
    if len(game_data["players"][user_id]) + num_cartelle > max_cartelle:
        return f"❌ Puoi acquistare al massimo {max_cartelle} cartelle per questa partita."
    
    # Aggiunge nuove cartelle alla partita attuale
    nuove_cartelle = [generate_bingo_card() for _ in range(num_cartelle)]
    game_data["players"][user_id].extend(nuove_cartelle)
    
    save_game_data(game_data)
    print(f"🎟️ Debug: {user_id} ha acquistato {num_cartelle} cartelle.")  # 🔴 DEBUG
    
    # Format output: mostra tutte le cartelle acquistate
    cartelle_testo = "\n\n".join(
        [f"📜 Cartella {i+1}:\n{format_bingo_card(cartella)}"
        for i, cartella in enumerate(nuove_cartelle)]
        )
    return f"✅ Hai acquistato {num_cartelle} cartelle per la partita corrente!\n\n{cartelle_testo}"

# Funzione per generare una cartella di Bingo 90
def generate_bingo_card():
    card = [[0] * 9 for _ in range(3)]  # Inizializza una griglia 3x9 con zeri
    columns = [list(range(i * 10 + 1, i * 10 + 11)) for i in range(9)]
    for col in columns:
        random.shuffle(col)
        
    filled_positions = set()
    for row in range(3):
        while len(filled_positions) < (5 * (row + 1)):
            col = random.randint(0, 8)
            if (row, col) not in filled_positions:
                card[row][col] = columns[col].pop()
                filled_positions.add((row, col))
    
    return card

#funzione per verificare i vincitori
def check_winners(game_data):
    """
    Controlla se ci sono vincitori di Cinquina o Bingo e aggiorna lo stato del gioco.
    """
    winners = {"Cinquina": [], "Bingo": []}
    
    for user_id, cards in game_data["players"].items():
        for card in cards:
            if check_cinquina(card, game_data["drawn_numbers"]) and user_id not in winners["Cinquina"]:
                winners["Cinquina"].append(user_id)
                
            if check_bingo(card, game_data["drawn_numbers"]) and user_id not in winners["Bingo"]:
                winners["Bingo"].append(user_id)
                
    if winners["Bingo"]:
        game_data["game_active"] = False
        save_game_data(game_data)
        
    return winners

#funzione per verificare la cinquina
def check_cinquina(card, drawn_numbers):
    """
    Controlla se una riga intera della cartella ha 5 numeri estratti (Cinquina).
    """
    for row in card:
        if sum(1 for num in row if num in drawn_numbers) == 5:  # ✅ Controlla se tutti i 5 numeri di una riga sono stati estratti
            return True
    return False

def check_bingo(card, drawn_numbers):
    """
    Controlla se tutti i 15 numeri della cartella sono stati estratti (Bingo).
    """
    return sum(1 for row in card for num in row if num in drawn_numbers) == 15  # ✅ Controlla se tutti i numeri della cartella sono stati estratti


# Funzione per formattare la cartella di Bingo in output leggibile
def format_bingo_card(card, drawn_numbers=None):
    """
    Formatta la cartella di Bingo con un layout migliorato per Telegram.
    
    - I numeri estratti hanno il simbolo ✅ sopra di loro.
    - I numeri sono allineati correttamente.
    - Usa `parse_mode="HTML"` per il supporto Telegram.
    """
    if drawn_numbers is None:
        drawn_numbers = []
        
    formatted_rows = []
    for row in card:
        formatted_row = []
        for num in row:
            if num in drawn_numbers:
                formatted_row.append(f"✅<b>{num:2}</b>")  # 🔥 Numeri estratti evidenziati con ✅ 
            elif num != 0:
                formatted_row.append(f"{num:2}")  # 🔹 Mantiene l'allineamento
            else:
                formatted_row.append("  ")  # 🔹 Spazio vuoto per un formato pulito
        formatted_rows.append(" | ".join(formatted_row))
        
    return "\n".join(formatted_rows)


if __name__ == "__main__":
    print(start_game())
