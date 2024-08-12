from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    id: str
    role: str