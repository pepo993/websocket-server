import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import config
import subprocess
import websockets
import json

# Connettiti al WebSocket per ricevere aggiornamenti sul gioco
async def listen_for_updates():
    uri = "wss://websocket-server-5muq.onrender.com/ws"

    #uri = "ws://localhost:8002/ws"  # WebSocket Server
    
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                message = await websocket.recv()  # Ricevi dati dal WebSocket
                data = json.loads(message)
                
                # Invia notifiche ai giocatori
                await notify_players(data)
            except Exception as e:
                print(f"⚠️ Errore WebSocket: {e}")

async def notify_players(data):
    """
    Invia notifiche ai giocatori con le cartelle aggiornate.
    """
    from game_logic import load_game_data, format_bingo_card
    
    numero_estratto = data["numero_estratto"]
    game_data = load_game_data()
    
    message = f"""
🔔 <b>📢 AGGIORNAMENTO BINGOTON!</b>

🎯 <b>Numero estratto:</b> {numero_estratto}
🎟️ <b>Cartelle vendute:</b> {data['game_status']['cartelle_vendute']}
💰 <b>Jackpot:</b> {data['game_status']['jackpot']} TON
👥 <b>Giocatori attivi:</b> {data['game_status']['giocatori_attivi']}

🔄 <i>Il gioco è in corso, ecco le tue cartelle aggiornate! 🍀</i>
"""

    for user_id, cards in game_data["players"].items():
        formatted_cards = "\n\n".join(format_bingo_card(card, game_data["drawn_numbers"]) for card in cards)
        
        try:
            await bot.send_message(user_id, message + "\n📜 <b>Le tue cartelle:</b>\n\n" + formatted_cards, parse_mode="HTML")
        except Exception as e:
            print(f"⚠️ Errore nell'invio delle cartelle a {user_id}: {e}")
            
    # Invia il messaggio a tutti i giocatori attivi
    from game_logic import load_game_data
    game_data = load_game_data()
    
    for user_id in game_data["players"]:
        try:
            await bot.send_message(user_id, message, parse_mode="HTML")
        except Exception as e:
            print(f"⚠️ Errore invio notifica a {user_id}: {e}")


# Avvia il task scheduler in background
subprocess.Popen(['python', 'game_scheduler.py'])

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: Message):
    commands_list = """
🎉 <b>Benvenuto nel BINGOTON! 🏆</b>
🎲 <i>Prepara le cartelle, sfida la sorte e vinci TON!</i> 🚀💰

🔹 <b>Come giocare?</b>
1️⃣ Acquista le cartelle 🎟️
2️⃣ Segui le estrazioni dei numeri 🔢
3️⃣ Vinci premi in TON! 💸

👇 <b>Ecco tutti i comandi disponibili:</b>

✅ <b>🎮 Comandi di gioco:</b>
🎟️ /buy [N] - Acquista <b>N</b> cartelle (default: 1)
📊 /game_status - Visualizza i giocatori attivi e cartelle totali
💰 /jackpot - Controlla il <b>montepremi</b> e i numeri estratti

💵 <b>🏦 Comandi finanziari:</b>
💳 /balance - Controlla il <b>saldo disponibile</b> in TON
🏧 /deposit - <b>Deposita</b> i tuoi fondi sul tuo wallet in game 
🏧 /withdraw - <b>Preleva</b> i tuoi fondi direttamente nel wallet

ℹ️ <b>📜 Info:</b>
🌐 /webapp - Apri la Web App
❓ /help - Visualizza la guida ai comandi

🎯 <i>Buona fortuna e che il Bingo sia con te! 🍀🔥</i>
"""

    await message.answer(commands_list, parse_mode="HTML")
    

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
@dp.message(Command("webapp"))
async def send_webapp_button(message: Message):
    webapp_url = config.WEBAPP_URL

    # Verifica che il link della Web App sia definito
    if not webapp_url or not webapp_url.startswith("https"):
        await message.answer("❌ Errore: Web App URL non valido. Controlla la configurazione.")
        return

    # Crea il pulsante solo se il link è valido
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Apri Web App", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await message.answer("Clicca qui per aprire la Web App:", reply_markup=keyboard)


    
@dp.message(Command("game_status"))
async def game_status_command(message: Message):
    from game_logic import load_game_data
    
    game_data = load_game_data()
    
    num_giocatori = len(game_data["players"])  # Numero di giocatori attivi
    num_cartelle = sum(len(cartelle) for cartelle in game_data["players"].values())  # Numero totale di cartelle acquistate
    
    response = f"📊 <b>Stato della partita:</b>\n\n👥 Giocatori attivi: <b>{num_giocatori}</b>\n🎟️ Cartelle totali acquistate: <b>{num_cartelle}</b>"
    
    await message.answer(response, parse_mode="HTML")

@dp.message(Command("buy"))
async def buy_ticket_command(message: Message):
    from game_logic import buy_ticket
    from transaction import get_user_balance, withdraw_funds
    
    args = message.text.split()
    num_cartelle = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    costo_totale = num_cartelle * config.COSTO_CARTELLA
    
    if balance < costo_totale:
        await message.answer(f"❌ Saldo insufficiente. Ti servono almeno {costo_totale} {config.CURRENCY}.")
        return
    
    withdraw_funds(user_id, costo_totale)  # Scala il saldo
    response = buy_ticket(user_id, num_cartelle)
    await message.answer(response)
    
    from game_logic import buy_ticket, load_game_data
    from transaction import get_user_balance
    
    user_id = message.from_user.id
    
    # Recupera l'ID della partita attuale
    game_data = load_game_data()
    if not game_data["game_active"]:
        await message.answer("❌ Nessuna partita attiva. Attendi l'inizio della prossima partita!")
        return
    
    # Estrai il numero di cartelle richiesto (default: 1)
    args = message.text.split()
    num_cartelle = 1  
    if len(args) > 1 and args[1].isdigit():
        num_cartelle = int(args[1])
        
    # Verifica saldo utente prima dell'acquisto
    costo_totale = num_cartelle * 1  # 1 TON per cartella
    saldo = get_user_balance(user_id)
    if saldo < costo_totale:
        await message.answer(f"❌ Saldo insufficiente! Ti servono almeno {costo_totale} TON per acquistare {num_cartelle} cartelle.")
        return
    
    # Effettua l'acquisto
    response = buy_ticket(user_id, num_cartelle)
    await message.answer(response)

@dp.message(Command("withdraw"))
async def withdraw_command(message: Message):
    from transaction import get_user_balance, withdraw_funds
    
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    args = message.text.split()
    if len(args) < 2 or not args[1].replace('.', '', 1).isdigit():
        await message.answer("❌ Usa il comando nel formato: <code>/withdraw 5</code>", parse_mode="HTML")
        return
    
    amount = float(args[1])  # Converti l'importo in float
    
    if amount <= 0:
        await message.answer("❌ L'importo deve essere maggiore di zero.")
        return
    
    if amount > balance:
        await message.answer(f"❌ Fondi insufficienti. Il tuo saldo attuale è di {balance} TON.")
        return
    result = withdraw_funds(user_id, amount)  # Preleva solo l'importo richiesto
    await message.answer(result)


@dp.message(Command("jackpot"))
async def jackpot_command(message: Message):
    from game_logic import load_game_data
    
    game_data = load_game_data()
    jackpot = len(game_data["players"]) * config.COSTO_CARTELLA
    numeri_estratti = game_data["drawn_numbers"]
    
    response = f"💰 <b>Jackpot attuale:</b> {jackpot} {config.CURRENCY}\n" \
            f"🎰 <b>Numeri estratti:</b> {', '.join(map(str, numeri_estratti)) if numeri_estratti else 'Nessuno'}"
            
    await message.answer(response, parse_mode="HTML")

# Comando per visualizzare il saldo
@dp.message(Command("balance"))
async def balance_command(message: Message):
    from transaction import get_user_balance
    
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    await message.answer(f"💰 Il tuo saldo disponibile: <b>{balance} TON</b>", parse_mode="HTML")

# Comando per simulare un deposito
@dp.message(Command("deposit"))
async def deposit_command(message: Message):
    from transaction import deposit_funds
    
    user_id = message.from_user.id
    args = message.text.split()
    amount = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 10  # Default 10 TON
    
    response = deposit_funds(user_id, amount)
    await message.answer(response)


# Comando per simulare un prelievo
@dp.message(Command("withdraw"))
async def withdraw_command(message: Message):
    from transaction import get_user_balance, withdraw_funds
    
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    
    # Verifica se il messaggio contiene un importo
    args = message.text.split()
    amount = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else balance
    
    if amount > balance:
        await message.answer(f"❌ Fondi insufficienti. Il tuo saldo è {balance} TON.")
        return
    
    result = withdraw_funds(user_id, amount)  # Preleva solo l'importo specificato
    await message.answer(result)


async def main():
    logging.basicConfig(level=logging.INFO)
    try:
        # Avvia il listener per le notifiche in parallelo
        asyncio.create_task(listen_for_updates())
        
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Errore nel bot: {e}")


if __name__ == '__main__':
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
