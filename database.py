from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    language = Column(Enum("urdu", "english"), nullable=False, default="english")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="store")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    customer_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    order_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum("pending", "confirmed", "cancelled", "no_response"), nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    store = relationship("Store", back_populates="orders")


class CustomerName(Base):
    __tablename__ = "customer_names"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OrderAmount(Base):
    __tablename__ = "order_amounts"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)
