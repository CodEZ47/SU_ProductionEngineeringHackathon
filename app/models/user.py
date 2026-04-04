from peewee import CharField, DateTimeField, AutoField
from datetime import datetime
from app.database import BaseModel

class User(BaseModel):
    id = AutoField()
    username = CharField()
    email = CharField(unique=True)
    created_at = DateTimeField(default=datetime.now)

