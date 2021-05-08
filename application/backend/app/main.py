from fastapi import FastAPI, Depends
from starlette.requests import Request
import uvicorn
import datetime
import os
import subprocess

from app.api.api_v1.routers.users import users_router
from app.api.api_v1.routers.auth import auth_router
from app.api.api_v1.routers.notes import notes_router

from app.core import config
from app.db.session import SessionLocal
from app.core.auth import get_current_active_user

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


# Initialize app, with default rate limiting for all endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["1/second"])
app = FastAPI(
    title=config.PROJECT_NAME, docs_url="/api/docs", openapi_url="/api"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response

#
# Get encrypted DB snapshot
#
@app.get("/getsnapshot")
async def root():
    now = datetime.datetime.now().strftime("%I:%M:%S %p")
    BUPASS = os.environ['BACKUP_PASS']
    DBUSER = os.environ['POSTGRESQL_USERNAME']
    DB = os.environ['POSTGRESQL_DATABASE']
    # this is needed for postgresql backup
    os.environ['PGPASSWORD'] = os.environ['POSTGRESQL_PASSWORD']
    f = open("sqldump.sql", 'w')
    #$pg_dump -h pgpool -p 5432 -U customuser -W  -d customdbatabase > dbout.sql

    cmd=['pg_dump', '-h', 'pgpool', '-p', '5432', '-U', DBUSER, '-W', '-d', DB]
    print(cmd)
    #subprocess.call(['pg_dump', '-h', 'pgpool', '-p', '5432' '-U', DBUSER, '-W', '-d', DB], stdout=f)
    subprocess.call(cmd, stdout=f)
    # Now zip it up
    subprocess.call(['zip',  '--encrypt', 'dbout.zip', 'sqldump.sql', '-P', BUPASS])
    file_path='dbout.zip' 
    return FileResponse(path=file_path, filename=file_path, media_type='application/octet-stream')



@app.get("/api/v1")
async def root():
    now = datetime.datetime.now().strftime("%I:%M:%S %p")
    return {"message": f"{now}: Hello World!"}


# Routers
app.include_router(
    users_router,
    prefix="/api/v1",
    tags=["users"],
    dependencies=[Depends(get_current_active_user)],
)
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(notes_router, prefix="/api/v1", tags=["notes"])

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8888)
