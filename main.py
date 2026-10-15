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
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

# ------------------------------------------------------------------
# Your personal values (change only if the assignment gave different ones)
# ------------------------------------------------------------------
ALLOWED_ORIGIN = "https://app-zy93ko.example.com"
# Also allow the exam page itself so the grader can test from the browser.
# Replace this with the real exam origin if the platform shows you one.
EXAM_ORIGIN = "https://exam.sanand.workers.dev"   # ← put the real one if you know it

RATE_LIMIT = 15          # B = 15 requests
WINDOW_SECONDS = 10      # every 10 seconds

# ------------------------------------------------------------------
# Middleware 1 – Request Context
# ------------------------------------------------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Re-use header if present, otherwise create a new UUID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store it so the endpoint can read it later
        request.state.request_id = request_id

        # Call the next middleware / endpoint
        response = await call_next(request)

        # Always put the same ID back in the response header
        response.headers["X-Request-ID"] = request_id
        return response

# ------------------------------------------------------------------
# Middleware 2 – Rate Limiter (per X-Client-Id)
# ------------------------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # client_id → list of timestamps of recent requests
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()

        # Keep only the timestamps that are still inside the 10-second window
        self.requests[client_id] = [
            t for t in self.requests[client_id]
            if now - t < WINDOW_SECONDS
        ]

        # Too many requests?
        if len(self.requests[client_id]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        # Record this request
        self.requests[client_id].append(now)

        # Let the request continue
        return await call_next(request)

# ------------------------------------------------------------------
# Add the three middlewares (order matters!)
# ------------------------------------------------------------------
# Innermost first → outermost last
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN, EXAM_ORIGIN],   # NO wildcard *
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ------------------------------------------------------------------
# The only endpoint
# ------------------------------------------------------------------
@app.get("/ping")
async def ping(request: Request):
    # Replace this with YOUR real logged-in email
    my_email = "24f3004884@ds.study.iitm.ac.in"

    return {
        "email": my_email,
        "request_id": request.state.request_id
    }
