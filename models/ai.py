import re

from pydantic import BaseModel

from models.result import ReturnResult

class AIResult(BaseModel):
    items : list[ReturnResult]