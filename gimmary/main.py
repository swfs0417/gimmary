from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

from gimmary.api import api_router

app = FastAPI()

app.include_router(api_router, prefix="/api")

@app.get('/health')
def health():
  return 'ok'