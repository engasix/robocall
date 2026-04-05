from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, DateTime, Numeric, Time, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone, time
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
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    language = Column(Enum("urdu", "english"), nullable=False, default="english")
    password_hash = Column(String(255), nullable=True)
    api_key_hash = Column(String(64), nullable=True)
    webhook_url = Column(String(500), nullable=True)   # store's callback URL for status updates
    timezone = Column(String(50), nullable=False, default="Asia/Karachi")
    call_window_start = Column(Time, nullable=False, default=time(9, 0))
    call_window_end = Column(Time, nullable=False, default=time(21, 0))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="store")


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        UniqueConstraint("store_id", "order_number", name="uq_store_order_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    order_number = Column(String(100), nullable=True)   # external reference (Shopify, WooCommerce, etc.)
    customer_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    order_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum("pending", "confirmed", "cancelled", "no_response"), nullable=False, default="pending")
    call_attempts = Column(Integer, nullable=False, default=0)  # incremented by scheduler each time a call is fired
    retry_count = Column(Integer, nullable=False, default=0)    # deprecated — use call_attempts
    next_retry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    store = relationship("Store", back_populates="orders")


class CustomerName(Base):
    __tablename__ = "customer_names"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    language = Column(Enum("urdu", "english"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OrderAmount(Base):
    __tablename__ = "order_amounts"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    language = Column(Enum("urdu", "english"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)
    # Add password_hash column if it doesn't exist (safe migration)
    # with engine.connect() as conn:
    #     conn.execute(
    #         "ALTER TABLE stores ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"
    #     )
    #     conn.commit()
