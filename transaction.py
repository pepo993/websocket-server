import json
import os
import config  # Importa la configurazione

# File per simulare le transazioni
tx_data_file = "data/transactions.json"

# Funzione per caricare le transazioni (simulato)
def load_transactions():
    if os.path.exists(tx_data_file):
        with open(tx_data_file, "r") as file:
            return json.load(file)
    return {}

# Funzione per salvare le transazioni (simulato)
def save_transactions(data):
    with open(tx_data_file, "w") as file:
        json.dump(data, file, indent=4)
    print(f"✅ Transazioni salvate correttamente: {data}")  # DEBUG

# Simula la richiesta del saldo
def get_user_balance(user_id):
    """Restituisce il saldo attuale dell'utente calcolando depositi - prelievi."""
    transactions = load_transactions()
    print(f"🔍 Lettura saldo utente {user_id}: {transactions.get(str(user_id), {'deposits': 0, 'withdrawals': 0})}")  # Debug
    user_data = transactions.get(str(user_id), {"deposits": 0, "withdrawals": 0})
    return user_data["deposits"] - user_data["withdrawals"]



# Quando stampi messaggi di transazioni, usa:
def deposit_funds(user_id, amount):
    transactions = load_transactions()
    user_id = str(user_id)  # Assicura che l'ID sia una stringa
    
    if user_id not in transactions:
        transactions[user_id] = {"deposits": 0, "withdrawals": 0}
    print(f"🔍 Prima del deposito: {transactions[user_id]}")  # DEBUG
    transactions[user_id]["deposits"] += amount  # ✅ CORRETTO: Somma invece di sovrascrivere
    save_transactions(transactions)
    print(f"✅ Dopo il deposito: {transactions[user_id]}")  # DEBUG
    return f"✅ Simulato deposito di {amount} {config.CURRENCY}"



#invia pagamento
def send_payment(user_id, amount, currency):
    """
    Simula il pagamento al vincitore.
    """
    print(f"🔍 Debug - Pagamento di {amount} {currency} a {user_id}")
    if amount > 0:
        return True  # Simuliamo un pagamento riuscito
    return False

#salva vittoria
def save_win(user_id, game_id, win_type, amount):
    """
    Registra una vincita per l'utente.
    """
    print(f"🏆 Vincita registrata! {user_id} ha vinto {win_type} per {amount} TON nella partita {game_id}.")


# Simula il prelievo di fondi
def withdraw_funds(user_id, amount):
    """
    Simula il prelievo di una quantità specifica di TON dall'utente.
    """
    transactions = load_transactions()
    user_id = str(user_id)
    if user_id not in transactions:
        return "❌ Nessun saldo disponibile."
    saldo_attuale = transactions[user_id]["deposits"] - transactions[user_id]["withdrawals"]
    print(f"🔍 Saldo PRIMA del prelievo per {user_id}: {saldo_attuale} TON")  # Debug
    if amount > saldo_attuale:
        print(f"❌ Errore: L'utente {user_id} ha tentato di prelevare {amount} TON, ma ha solo {saldo_attuale} TON.")  # Debug
        return f"❌ Fondi insufficienti. Il tuo saldo attuale è di {saldo_attuale} TON."
    
    # ✅ Sottraiamo solo l'importo richiesto senza arrotondamenti errati
    transactions[user_id]["withdrawals"] += amount
    save_transactions(transactions)
    saldo_aggiornato = transactions[user_id]["deposits"] - transactions[user_id]["withdrawals"]
    print(f"✅ Prelievo riuscito! Saldo DOPO il prelievo per {user_id}: {saldo_aggiornato} TON")  # Debug

    return f"✅ Prelievo confermato di {amount} TON. Saldo rimanente: {saldo_aggiornato} TON"


def update_user_balance(user_id, new_balance):
    """
    Aggiorna direttamente il saldo dell'utente nel file JSON.
    """
    transactions = load_transactions()
    user_id = str(user_id)
    
    if user_id not in transactions:
        transactions[user_id] = {"deposits": 10, "withdrawals": 0}  # Default 10 TON
        
    current_balance = transactions[user_id]["deposits"] - transactions[user_id]["withdrawals"]
    difference = new_balance - current_balance
    
    if difference > 0:
        transactions[user_id]["deposits"] += difference  # Aggiunge fondi
    elif difference < 0:
        transactions[user_id]["withdrawals"] += abs(difference)  # Sottrae fondi
    save_transactions(transactions)
    return f"✅ Saldo aggiornato: {new_balance} TON"

if __name__ == "__main__":
    print("✅ La logica è in modalità simulata. Nessuna transazione reale viene eseguita.")
