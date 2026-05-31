from pydantic import BaseModel


class ReturnResult(BaseModel):
    title: str
    link: str
    price: int  # в рублях, без символов и пробелов
    description: str | None = None
    photo_url: str | None = None
    source: str = ""  # avito | ozon | autopiter | rusmarket