from peewee import CharField, DateTimeField, ForeignKeyField, AutoField, TextField
from datetime import datetime
from app.database import BaseModel
from app.models.url import URL
from app.models.user import User

class Event(BaseModel):
    id = AutoField(primary_key=True)
    url = ForeignKeyField(URL, backref="events")
    user = ForeignKeyField(User, backref="events")
    event_type = CharField()
    timestamp = DateTimeField(default=datetime.now)
    details = TextField()