import pytest
from app import create_app
from app.database import db
from app.models.user import User
from app.models.url import URL
from app.models.event import Event


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.connect(reuse_if_open=True)

        # Start every test from a clean database state
        db.drop_tables([Event, URL, User], safe=True)
        db.create_tables([User, URL, Event], safe=True)

        # Seed one user for tests
        User.create(
            id=1,
            username="testuser",
            email="test@test.com"
        )

        # Reset Postgres sequences so future inserts do not collide
        db.execute_sql("""
            SELECT setval(
                pg_get_serial_sequence('"user"', 'id'),
                COALESCE((SELECT MAX(id) FROM "user"), 1),
                true
            );
        """)
        db.execute_sql("""
            SELECT setval(
                pg_get_serial_sequence('"url"', 'id'),
                COALESCE((SELECT MAX(id) FROM "url"), 1),
                true
            );
        """)
        db.execute_sql("""
            SELECT setval(
                pg_get_serial_sequence('"event"', 'id'),
                COALESCE((SELECT MAX(id) FROM "event"), 1),
                true
            );
        """)

    yield app

    with app.app_context():
        if not db.is_closed():
            db.close()


@pytest.fixture
def client(app):
    return app.test_client()