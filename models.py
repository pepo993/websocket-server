from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# 📌 Modello per la tabella utenti
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language = Column(String, nullable=True)
    balance = Column(Float, default=0.0)  # Saldo in TON
    games_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    date_registered = Column(DateTime, default=func.now())  # Usa func.now() per ottenere l'ora del database

    # 📌 Relazioni con altre tabelle
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete")


# 📌 Modello per la tabella partite
class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_id = Column(String, unique=True, index=True, nullable=False)
    active = Column(Boolean, default=True)
    jackpot = Column(Float, default=0.0)
    drawn_numbers = Column(String, default="")  # Numeri estratti salvati come stringa
    start_time = Column(DateTime, default=func.now())  # Tempo di inizio della partita
    end_time = Column(DateTime, nullable=True)  # Tempo di fine della partita

    # 📌 Relazione con Ticket (una partita ha più cartelle)
    tickets = relationship("Ticket", back_populates="game", cascade="all, delete")


# 📌 Modello per la tabella cartelle di gioco (Tickets)
class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    numbers = Column(String, nullable=False)  # Cartella in formato stringa (numeri separati da virgole)
    purchase_time = Column(DateTime, default=func.now())

    # 📌 Relazioni
    game = relationship("Game", back_populates="tickets")
    user = relationship("User", back_populates="tickets")


# 📌 Modello per la tabella transazioni
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String, nullable=False)  # deposit, withdraw, win
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    # 📌 Relazione con User
    user = relationship("User", back_populates="transactions")
