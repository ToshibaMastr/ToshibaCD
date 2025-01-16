from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship

from .base_class import SQLAlchemyBaseModel


class Server(AsyncAttrs, SQLAlchemyBaseModel):
    __tablename__ = "servers"
    __table_args__ = {"schema": "game_servers"}

    # Info
    identifier = Column(String, unique=True, nullable=False)
    info = Column(
        JSON,
        nullable=False,
        default={"ru": {"title": ""}, "en": {"title": ""}, "common": {"logo": ""}},
    )

    # Added info
    params = Column(
        JSON, nullable=False, default={"max_online": 20, "gameversion": "1.12.2"}
    )

    status_id = Column(
        Integer,
        ForeignKey("game_servers.server_statuses.id", ondelete="CASCADE"),
        nullable=False,
    )
    endpoint_id = Column(
        Integer,
        ForeignKey("game_servers.endpoints.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = relationship("ServerStatus", back_populates="servers", lazy="selectin")
    endpoint = relationship("Endpoint", back_populates="servers", lazy="selectin")


class Endpoint(AsyncAttrs, SQLAlchemyBaseModel):
    __tablename__ = "endpoints"
    __table_args__ = {"schema": "game_servers"}

    ip = Column(String, nullable=False)
    port = Column(Integer, default=25565, nullable=False)
    host = Column(String, nullable=False)

    servers = relationship(
        "Server",
        back_populates="endpoint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ServerStatus(AsyncAttrs, SQLAlchemyBaseModel):
    __tablename__ = "server_statuses"
    __table_args__ = {"schema": "game_servers"}

    online = Column(Integer, default=0, nullable=False)
    status = Column(String, default="Inactive", nullable=False)
    tpc = Column(Integer, default=0, nullable=False)

    servers = relationship("Server", back_populates="status", lazy="selectin")


class User(SQLAlchemyBaseModel):
    __tablename__ = "users"

    name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    subscribers = Column(Integer, default=0, nullable=False)
