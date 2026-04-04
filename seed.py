import csv
from datetime import datetime

from app import create_app
from app.database import db
from app.models.user import User
from app.models.url import URL
from app.models.event import Event


def parse_datetime(value):
    return datetime.fromisoformat(value.strip())


def parse_bool(value):
    return value.strip().lower() in ("true", "1", "t", "yes")


app = create_app()

with app.app_context():
    db.connect(reuse_if_open=True)

    db.create_tables([User, URL, Event])

    # Optional: clear old data before reseeding
    Event.delete().execute()
    URL.delete().execute()
    User.delete().execute()

    with open("data/users.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            User.create(
                id=int(row["id"]),
                username=row["username"],
                email=row["email"],
                created_at=parse_datetime(row["created_at"]),
            )

    with open("data/urls.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            URL.create(
                id=int(row["id"]),
                user=int(row["user_id"]),
                short_code=row["short_code"],
                original_url=row["original_url"],
                title=row["title"] or None,
                is_active=parse_bool(row["is_active"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"]),
            )

    with open("data/events.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            Event.create(
                id=int(row["id"]),
                url=int(row["url_id"]),
                user=int(row["user_id"]),
                event_type=row["event_type"],
                timestamp=parse_datetime(row["timestamp"]),
                details=row["details"],
            )

    db.close()

print("Seed completed successfully.")