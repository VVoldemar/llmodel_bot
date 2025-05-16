import datetime
import sqlalchemy as sa
import sqlalchemy.orm as orm

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)  # tg id
    username = sa.Column(sa.String, unique=True, nullable=False)  # @tg_account
    registered_at = sa.Column(sa.DateTime, default=lambda: datetime.datetime.now(), nullable=False)

    referrer_id = sa.Column(sa.Integer, sa.ForeignKey(id), default=None, nullable=True)
    is_banned = sa.Column(sa.Boolean, default=False, nullable=False)

    # Ai models
    context_mode_on: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=True, nullable=False)
    instruction_mode_on: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, nullable=False)
    selected_model: orm.Mapped[str | None] = orm.mapped_column(sa.String, nullable=True)
    instruction: orm.Mapped[str | None] = orm.mapped_column(sa.String, nullable=True)

    referrer = orm.relationship("User", back_populates="referrals", remote_side=[id])
    referrals = orm.relationship("User", back_populates="referrer")

    messages = orm.relationship("Message", back_populates="owner")
    # subscriptions = orm.relationship("UserSubscription", back_populates="user")

    # def has_active_subscription(self):
    #     return any(sub.is_active() for sub in self.subscriptions)

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}')"