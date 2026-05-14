# schemas/student.py
from pydantic import BaseModel, Field
from typing import Optional

class StudentCreate(BaseModel):
    id: int = Field(gt=0, lt=150)
    username: str = Field(min_length=2, max_length=100)
    password: str

class StudentResponse(BaseModel):
    id: int
    username: str
    password: str

    class Config:
        from_attributes = True