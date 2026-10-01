from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    filename = Column(String)
    subject = Column(String)
    sender = Column("from", String)
    verdict = Column(String, index=True)
    risk_score = Column(Float)
    result_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class IOC(Base):
    __tablename__ = "iocs"
    __table_args__ = (UniqueConstraint("type", "value"),)

    id = Column(Integer, primary_key=True)
    type = Column(String, index=True)  # domain | url | ip | sha256
    value = Column(String, index=True)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    hit_count = Column(Integer, default=0)
    max_verdict = Column(String)


class TICache(Base):
    __tablename__ = "ti_cache"
    __table_args__ = (UniqueConstraint("source", "key"),)

    id = Column(Integer, primary_key=True)
    source = Column(String)
    key = Column(String, index=True)
    result_json = Column(Text)
    fetched_at = Column(DateTime(timezone=True))
