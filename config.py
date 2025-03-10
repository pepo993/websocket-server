# Configurazione del bot Telegram e Web App
from dotenv import load_dotenv
import os

# Carica le variabili d'ambiente
load_dotenv()

# URL del database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@postgres.railway.internal:5432/railway")

# Token del bot Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# URL della Web App Telegram
WEBAPP_URL = "https://telegram-bingo-bot.vercel.app"

# Debug: Stampiamo il valore del token per verificare se Railway lo sta leggendo
print(f"DEBUG: TELEGRAM_BOT_TOKEN = {TELEGRAM_BOT_TOKEN}")

# Controllo se il token è stato caricato correttamente
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("❌ ERRORE: TELEGRAM_BOT_TOKEN non è stato trovato nelle variabili d'ambiente!")

# Impostazioni finanziarie
CURRENCY = "TON"  # Puoi modificarlo in base al token usato
COSTO_CARTELLA = 0.2  # Prezzo di una cartella
FEE_PERCENTUALE = 0.10  # Percentuale trattenuta dal sistema (10%)
JACKPOT_BINGO = 0.90  # Percentuale destinata al vincitore del Bingo (90%)
JACKPOT_CINQUINA = 0.10  # Percentuale destinata al vincitore della Cinquina (10%)

# Limite massimo di cartelle acquistabili per giocatore
MAX_CARTELLE_PER_UTENTE = 24

# Timeout massimo per una partita
TIMEOUT_PARTITA = 600  # Tempo massimo per completare la partita (secondi)
