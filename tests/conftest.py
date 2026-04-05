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
        db.create_tables([User, URL, Event])

        User.create(id=1, username="test", email="test@test.com")

    yield app


@pytest.fixture
def client(app):
    return app.test_client()