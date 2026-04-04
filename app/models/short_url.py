import string
import random
from peewee import CharField, IntegerField, DateTimeField
from datetime import datetime

from app.database import BaseModel


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class ShortURL(BaseModel):
    original_url = CharField()
    short_code = CharField(unique=True)
    created_at = DateTimeField(default=datetime.now)
    click_count = IntegerField(default=0)