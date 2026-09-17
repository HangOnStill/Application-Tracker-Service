from pydantic import BaseModel


class DeleteResponse(BaseModel):
    deleted: bool = True
    id: int
