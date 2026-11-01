from pydantic import BaseModel


class DocumentVerifyRequest(BaseModel):
    status: str
    remarks: str
