from peewee import CharField, DateTimeField, IntegerField
from app.database import BaseModel

class User(BaseModel):
    id = IntegerField(primary_key=True)
    username = CharField()
    email = CharField(unique=True)
    created_at = DateTimeField()

