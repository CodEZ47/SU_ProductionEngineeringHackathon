import os
import time

from peewee import DatabaseProxy, Model, PostgresqlDatabase

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db

def connect_with_retry(db, retries=10, delay=2):
    for i in range(retries):
        try:
            db.connect(reuse_if_open=True)
            print("Connected to DB")
            return
        except Exception as e:
            print(f"DB not ready, retrying... ({i+1}/{retries})")
            time.sleep(delay)
    raise Exception("Could not connect to DB")


def init_db(app):
    database = PostgresqlDatabase(
        os.environ.get("DATABASE_NAME", "hackathon_db"),
        host=os.environ.get("DATABASE_HOST", "postgres"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
    )
    db.initialize(database)

    from app.models.user import User
    from app.models.url import URL
    from app.models.event import Event

    connect_with_retry(db)
    db.create_tables([User, URL, Event], safe=True)
    db.close()

    @app.before_request
    def _db_connect():
        connect_with_retry(db)

    @app.teardown_appcontext
    def _db_close(exc):
        if not db.is_closed():
            db.close()
