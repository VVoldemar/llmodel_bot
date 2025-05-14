import sqlalchemy as sa
import sqlalchemy.orm as orm
import logging

import settings

SqlAlchemyBase = sa.orm.declarative_base()

__factory = None


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise FileNotFoundError("DB filename are not specified")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    logging.info(f"Connection to db at the address {db_file}")

    engine = sa.create_engine(conn_str, echo=settings.DEBUG_MODE)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def get_session() -> sa.orm.Session:
    global __factory
    return __factory()