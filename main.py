'''import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI()

# Enable CORS for grader/browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 1: defaults
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Layer 2: YAML
if os.path.exists("config.development.yaml"):
    with open("config.development.yaml", "r") as f:
        yaml_config = yaml.safe_load(f)
        config.update(yaml_config)

# Layer 3: .env
env_port = os.getenv("APP_PORT")
env_workers = os.getenv("NUM_WORKERS")
env_debug = os.getenv("APP_DEBUG")

if env_port:
    config["port"] = int(env_port)
if env_workers:
    config["workers"] = int(env_workers)
if env_debug:
    config["debug"] = env_debug.lower() in ["true", "1", "yes", "on"]

# Layer 4: OS env vars (APP_* prefix)
os_port = os.getenv("APP_PORT")
os_workers = os.getenv("APP_WORKERS")
os_debug = os.getenv("APP_DEBUG")
os_log_level = os.getenv("APP_LOG_LEVEL")
os_api_key = os.getenv("APP_API_KEY")

if os_port:
    config["port"] = int(os_port)
if os_workers:
    config["workers"] = int(os_workers)
if os_debug:
    config["debug"] = os_debug.lower() in ["true", "1", "yes", "on"]
if os_log_level:
    config["log_level"] = os_log_level
if os_api_key:
    config["api_key"] = os_api_key

@app.get("/effective-config")
def get_config(set: list[str] = Query(default=[])):
    final_config = config.copy()

    # Apply CLI overrides (?set=key=value)
    for override in set:
        if "=" in override:
            key, value = override.split("=", 1)
            if key in ["port", "workers"]:
                final_config[key] = int(value)
            elif key == "debug":
                final_config[key] = value.lower() in ["true", "1", "yes", "on"]
            else:
                final_config[key] = value

    # Mask api_key
    final_config["api_key"] = "****"
    return final_config

import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 1: defaults
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Layer 2: YAML
with open("config.development.yaml", "r") as f:
    yaml_config = yaml.safe_load(f)
    config.update(yaml_config)

# Layer 3: .env
env_port = os.getenv("APP_PORT")
env_workers = os.getenv("NUM_WORKERS")
env_debug = os.getenv("APP_DEBUG")

if env_port:
    config["port"] = int(env_port)
if env_workers:
    config["workers"] = int(env_workers)
if env_debug:
    config["debug"] = env_debug.lower() in ["true", "1", "yes", "on"]

# Layer 4: OS env vars (APP_* prefix)
os_port = os.getenv("APP_PORT")
os_workers = os.getenv("APP_WORKERS")
os_debug = os.getenv("APP_DEBUG")
os_log_level = os.getenv("APP_LOG_LEVEL")
os_api_key = os.getenv("APP_API_KEY")

if os_port:
    config["port"] = int(os_port)
if os_workers:
    config["workers"] = int(os_workers)
if os_debug:
    config["debug"] = os_debug.lower() in ["true", "1", "yes", "on"]
if os_log_level:
    config["log_level"] = os_log_level
if os_api_key:
    config["api_key"] = os_api_key

@app.get("/effective-config")
def get_config(set: list[str] = Query(default=[])):
    final_config = config.copy()

    # Apply CLI overrides (?set=key=value)
    for override in set:
        if "=" in override:
            key, value = override.split("=", 1)
            if key in ["port", "workers"]:
                final_config[key] = int(value)
            elif key == "debug":
                final_config[key] = value.lower() in ["true", "1", "yes", "on"]
            else:
                final_config[key] = value

    # Mask api_key
    final_config["api_key"] = "****"
    return final_config'''
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

ALLOWED_ORIGIN = "https://app-zy93ko.example.com"
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

RATE_LIMIT = 15
WINDOW_SECONDS = 10

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        self.requests[client_id] = [
            t for t in self.requests[client_id] if now - t < WINDOW_SECONDS
        ]
        if len(self.requests[client_id]) >= RATE_LIMIT:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        self.requests[client_id].append(now)
        return await call_next(request)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN, EXAM_ORIGIN],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f3004884@ds.study.iitm.ac.in",
        "request_id": request.state.request_id
    }
