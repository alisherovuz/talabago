from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum


Base = declarative_base()


class PaperType(enum.Enum):
    referat = "referat"
    kurs = "kurs"
    diplom = "diplom"
    prezentatsiya = "prezentatsiya"


class OrderStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(200))
    university = Column(String(300))
    course = Column(Integer)  # 1, 2, 3, 4, 5, 6
    is_registered = Column(Integer, default=0)  # 0=no, 1=yes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String(500), nullable=False)
    paper_type = Column(Enum(PaperType), nullable=False)
    language = Column(String(10), default="uz")
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    price = Column(Integer, nullable=False)
    file_url = Column(String(500))
    word_count = Column(Integer)
    page_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    user = relationship("User", back_populates="orders")
