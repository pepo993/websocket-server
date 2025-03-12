from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)  # ✅ `telegram_id` è sempre una stringa
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language = Column(String, nullable=True)
    balance = Column(Float, default=0.0)  # Saldo in TON
    games_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    date_registered = Column(DateTime, default=func.now())
    wallet_address = Column(String, unique=True, nullable=True)  # ✅ Salva l'indirizzo del wallet TON dell'utente
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_id = Column(String, unique=True, index=True, nullable=False)  # ✅ `game_id` rimane STRING
    active = Column(Boolean, default=True)
    jackpot = Column(Float, default=0.0)
    drawn_numbers = Column(String, default="")  # Numeri estratti salvati come stringa
    start_time = Column(DateTime, default=func.now())  # Tempo di inizio della partita
    end_time = Column(DateTime, nullable=True)  # Tempo di fine della partita
    tickets = relationship("Ticket", back_populates="game", cascade="all, delete-orphan")

class TicketNumber(Base):
    __tablename__ = "ticket_numbers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)
    ticket = relationship("Ticket", back_populates="numbers_list")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    purchase_time = Column(DateTime, default=func.now())
    numbers_list = relationship("TicketNumber", back_populates="ticket", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)  # ✅ Mantiene `VARCHAR`
    transaction_type = Column(String, nullable=False)  # deposit, withdraw, win
    amount = Column(Float, nullable=False)
    system_fees = Column(Float, default=0.0)  # ✅ Traccia la quota trattenuta dal sistema
    timestamp = Column(DateTime, default=func.now())
    tx_hash = Column(String, unique=True, nullable=True)  # ✅ Hash della transazione TON per tracciabilità
    status = Column(String, default="pending")  # ✅ pending, confirmed, failed, cancelled
    user = relationship("User", back_populates="transactions")
