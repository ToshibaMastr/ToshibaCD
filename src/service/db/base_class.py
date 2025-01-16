from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SQLAlchemyBaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, nullable=False)

    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
