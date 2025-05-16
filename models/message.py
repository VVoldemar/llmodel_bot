import datetime
import sqlalchemy as sa
import sqlalchemy.orm as orm

from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    __tablename__ = "messages"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    owner_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey('users.id'))
    is_from_user: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, nullable=False, default=True)

    content: orm.Mapped[str] = orm.mapped_column(sa.String, nullable=False)

    owner = orm.relationship("User", back_populates="messages")