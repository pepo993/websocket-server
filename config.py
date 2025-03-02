# Configurazione del bot Telegram e Web App

from dotenv import load_dotenv
import os

# Carica le variabili d'ambiente dal file .env (se usato)
load_dotenv()

# Token del bot Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# URL della Web App Telegram (SOSTITUISCI con il tuo link!)
WEBAPP_URL = "https://telegram-bingo-bot.vercel.app"



# Impostazioni finanziarie
CURRENCY = "TON"  # Puoi modificarlo in base al token usato
COSTO_CARTELLA = 0.2  # Prezzo di una cartella
FEE_PERCENTUALE = 0.10  # Percentuale trattenuta dal sistema (10%)
JACKPOT_BINGO = 0.90  # Percentuale destinata al vincitore del Bingo (90%)
JACKPOT_CINQUINA = 0.10  # Percentuale destinata al vincitore della Cinquina (10%)

# Limite massimo di cartelle acquistabili per giocatore
MAX_CARTELLE_PER_UTENTE = 24

# Timeout massimo per una partita
TIMEOUT_PARTITA = 300  # Tempo massimo per completare la partita (secondi)
