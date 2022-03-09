import os

from fastapi import Form
from pydantic import BaseModel, validator


class FilePrepare(BaseModel):
    file_path: str

    @validator('file_path')
    def is_file_path_valid(cls, v):
        if not os.path.isfile(v):
            raise ValueError('Please try with a exact file path.')
        return v


class FileChunk(BaseModel):
    file_content: str


class Token(BaseModel):
    access_token: str
    token_type: str


class FinaliseForm:
    def __init__(self, filename: str = Form(...), fileSize: int = Form(...),
                 chunks: int = Form(...)):
        self.filename = filename
        self.fileSize = fileSize
        self.chunks = chunks

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "fileSize": self.fileSize,
            "chunks": self.chunks
        }
