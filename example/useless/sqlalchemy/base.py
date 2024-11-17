import logging

import pandas as pd
from sqlalchemy import delete, Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.sql import Insert


@compiles(Insert, "sqlite")
def sqlite_insert_ignore(insert, compiler, **kw):
    return compiler.visit_insert(insert.prefix_with("OR IGNORE"), **kw)


@compiles(Insert, "mysql")
def mysql_insert_ignore(insert, compiler, **kw):
    return compiler.visit_insert(insert.prefix_with("IGNORE"), **kw)


@compiles(Insert, "postgresql")
def postgresql_insert_ignore(insert, compiler, **kw):
    statement = compiler.visit_insert(insert, **kw)
    returning_position = statement.find("RETURNING")
    if returning_position >= 0:
        return (
            statement[:returning_position]
            + "ON CONFLICT DO NOTHING "
            + statement[returning_position:]
        )
    else:
        return statement + " ON CONFLICT DO NOTHING"


class Base(DeclarativeBase):
    pass


class BaseTable:
    def __init__(self, MyTable, engine: Engine, *args, **kwargs):
        self.table = MyTable
        self.engine: Engine = engine
        self.session = sessionmaker(self.engine)
        self.create()

    def create(self):
        self.table.metadata.create_all(self.engine)

    def execute(self, stmt):
        with self.engine.begin() as conn:
            return conn.execute(stmt)

    def select_all(self):
        with self.engine.begin() as conn:
            return pd.read_sql_table(self.table.__tablename__, conn)

    def delete_all(self):
        return self.execute(delete(self.table))

    def insert(self, values):
        with Session(self.engine) as session:
            try:
                session.bulk_insert_mappings(self.table, values)
                session.commit()
            except Exception as ex:
                logging.warning(ex)
                session.rollback()

    def update(self, values):
        with Session(self.engine) as session:
            try:
                session.bulk_update_mappings(self.table, values)
                session.commit()
            except Exception as ex:
                logging.warning(ex)
                session.rollback()

    def upsert(self, values):
        self.insert(values)
        self.update(values)
