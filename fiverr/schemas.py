from pydantic import BaseModel, HttpUrl, field_validator


class CreateLinkRequest(BaseModel):
    seller_id: str
    original_url: HttpUrl

    @field_validator('seller_id')
    @classmethod
    def seller_id_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('seller_id must not be blank')
        return stripped

    @field_validator('original_url', mode='before')
    @classmethod
    def strip_url(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v
