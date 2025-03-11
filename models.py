from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# 📌 Modello per la tabella utenti
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)  # ✅ Cambiato a Integer
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language = Column(String, nullable=True)
    balance = Column(Float, default=0.0)  # Saldo in TON
    games_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    date_registered = Column(DateTime, default=func.now())

    # 📌 Relazioni con altre tabelle
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, balance={self.balance})>"

# 📌 Modello per la tabella partite
class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_id = Column(String, unique=True, index=True, nullable=False)
    active = Column(Boolean, default=True)
    jackpot = Column(Float, default=0.0)
    drawn_numbers = Column(String, default="")  # Può essere convertito in una lista con un @property
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)

    # 📌 Relazione con Ticket (una partita ha più cartelle)
    tickets = relationship("Ticket", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, game_id={self.game_id}, active={self.active}, jackpot={self.jackpot})>"

# 📌 Modello per la tabella cartelle di gioco (Tickets)
class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)  # ✅ Ora è Integer
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    numbers = Column(String, nullable=False)
    purchase_time = Column(DateTime, default=func.now())

    # 📌 Relazioni
    game = relationship("Game", back_populates="tickets")
    user = relationship("User", back_populates="tickets")

    def __repr__(self):
        return f"<Ticket(id={self.id}, game_id={self.game_id}, user_id={self.user_id})>"

# 📌 Modello per la tabella transazioni
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # ✅ Ora è Integer
    transaction_type = Column(String, nullable=False)  # deposit, withdraw, win
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    # 📌 Relazione con User
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"
