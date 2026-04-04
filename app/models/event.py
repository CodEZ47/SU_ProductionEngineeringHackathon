from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField
from app.database import BaseModel
from app.models.url import URL
from app.models.user import User

class Event(BaseModel):
    id = IntegerField(primary_key=True)
    url = ForeignKeyField(URL, backref="events")
    user = ForeignKeyField(User, backref="events")
    event_type = CharField()
    timestamp = DateTimeField()
    details = TextField()  #it's a json {"shortcode":"XXX","original_url:"YYY"}