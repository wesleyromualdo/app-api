from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from src.utils import utils
import os, json
from dotenv import dotenv_values

config = dotenv_values(".env")
config = json.loads((json.dumps(config) ))

SQLALCHEMY_DATABASE_URL = config['DATABASE_URL_AUTOMAXIA']

#SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
connect_args = {
    "keepalives": config['KEEPALIVES'],
    "keepalives_idle": config['KEEPALIVES_IDLE'],
    "keepalives_interval": config['KEEPALIVES_INTERVAL'],
    "keepalives_count": config['KEEPALIVES_COUNT']
}

def set_timezone(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET TIME ZONE 'America/Sao_Paulo';")
    cursor.close()

#POOL_SIZE: O tamanho do pool a ser mantido, padronizado como 5. Este é o maior número de conexões que serão mantidas persistentemente no pool,
#    pode ser definido como 0 para indicar nenhum limite de tamanho

#MAX_OVERFLOW: O tamanho máximo de estouro do pool. Quando o número de conexões com check-out atingir o tamanho definido em pool_size, 
# serão retornadas conexões adicionais até esse limite. Quando essas conexões adicionais são retornadas ao pool, elas são desconectadas e descartadas
# max_overflow pode ser definido como -1 para indicar nenhum limite de estouro

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, connect_args=connect_args, 
                        pool_size=int(config['POOL_SIZE']), 
                        max_overflow=int(config['MAX_OVERFLOW']), 
                        pool_recycle=int(config['POOL_RECYCLE'])
                    )

SessionLocal = sessionmaker(autocommit=False, autoflush=config['AUTOFLUSH'], bind=engine, expire_on_commit=config['EXPIRE_ON_COMMIT'], future=True)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True, future=True)

# Adicionar o evento de engine connect
event.listen(engine, 'connect', set_timezone)


@event.listens_for(SessionLocal, 'after_begin')
def receive_after_begin(session, transaction, connection):
    session.execute("SET TIME ZONE 'America/Sao_Paulo';")

Base = declarative_base()

def criar_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def no_expire():
    db = SessionLocal()
    s = db.session()
    s.expire_on_commit = False
    try:
        yield
    finally:
        s.expire_on_commit = True