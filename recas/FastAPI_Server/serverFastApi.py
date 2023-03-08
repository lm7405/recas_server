from fastapi import FastAPI
from typing import Any, Dict
from pydantic import BaseModel


from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


class ServerFastApiConfig(BaseModel):
    specFile: Dict
    port: int


class ServerFastApi(FastAPI):
    def __init__(self, config: ServerFastApiConfig, debug, **extra: Any):
        super().__init__(**extra)
        self.config = config
        self.debug = debug
        self.mount("/documents", StaticFiles(directory="./documents"))
        self.set_cors()

    # -------------------------------------------------------------------------
    # CORS(Cross-Origin Resource Sharing)
    # cross-origin HTTP 요청을 제한하는 브라우저 보안기능
    # 참고 : https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/how-to-cors.html
    # -------------------------------------------------------------------------
    def set_cors(self):
        origins = [
            "http://127.0.0.1:" + str(self.config.port),
            "http://localhost:" + str(self.config.port)
        ]
        self.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
