from peewee import CharField, BooleanField, DateTimeField, ForeignKeyField, IntegerField
from app.database import BaseModel
from app.models.user import User

class URL(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="urls")
    short_code = CharField(unique=True)
    original_url = CharField()
    title = CharField(null=True)
    is_active = BooleanField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
