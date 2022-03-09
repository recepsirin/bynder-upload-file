import base64
import hmac
import math
from datetime import timedelta

from fastapi import (
    FastAPI, status, Request, Depends, HTTPException
)
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from services.auth_service import AuthService
from services.file_service import FileService
from services.mongo_client import MongoClient
from schemas import FilePrepare, FileChunk, Token, FinaliseForm
from tasks import upload_file, finalise_file
from utils import create_hex_digest

app = FastAPI(debug=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@app.post("/auth/token/", response_model=Token)
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    auth_service = AuthService(MongoClient("auth"))
    user = await auth_service.authenticate_user(form_data.username,
                                                form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.get('username')},
        expires_delta=access_token_expires)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"access_token": access_token, "token_type": "bearer"}
    )


@app.post("/upload/prepare/", dependencies=[Depends(oauth2_scheme)])
async def prepare(file_path: FilePrepare):
    fs = FileService()
    _id = await fs.prepare_upload_operation(
        name=fs.get_file_name(file_path.file_path),
        path=file_path.file_path,
        size=fs.get_file_size(file_path.file_path),
        mimetype=fs.get_mime_type(file_path.file_path)
    )
    upload_file.delay(_id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"file_id": _id}
    )


@app.post("/upload/{file_id}/chunk/{chunk_number}",
          dependencies=[Depends(oauth2_scheme)])
async def upload_chunks(file_id: str, chunk_number: int,
                        file_content: FileChunk, request: Request):
    content_sha_256 = request.headers.get("content-sha256")
    if not content_sha_256:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a key named content-sha256 and the file "
                   "hash generated with the sha256 algorithm as a value.")

    b_file_content = base64.b64decode(file_content.file_content)
    if not hmac.compare_digest(content_sha_256,
                               create_hex_digest("BYNDER-APP",
                                                 b_file_content)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="Please, ensure the chunk uploaded "
                                   "has it’s data's hex digest in the headers")
    fs = FileService()
    await fs.update_chunk(file_id, chunk_number, file_content.file_content)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"result": 'success'}
    )


@app.post("/upload/{file_id}/finalise", dependencies=[Depends(oauth2_scheme)])
async def finalise(file_id: str, request: Request,
                   body: FinaliseForm = Depends()):
    content_sha_256 = request.headers.get("content-sha256")
    if not content_sha_256:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a key named content-sha256 and the file "
                   "hash generated with the sha256 algorithm as a value.")

    fs = FileService()
    if not await fs.is_file_exist(file_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file could not be found that "
                   "the file_id you provided is not referenced to any file.")

    total_chunk = math.ceil(body.fileSize / 1048576)  # 1048576 = 1MB
    if not total_chunk == body.chunks:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="The number of total chunks you provided "
                                   "didn't matched with the exact one")

    finalise_file.delay(file_id, content_sha_256, body.to_dict())
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"Message": "The file will be uploading to the server"}
    )
