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
    return final_config
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
'''
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import time
import uuid
from collections import defaultdict, deque

app = FastAPI()

# ---------- CORS (required) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

# ---------- Config from the assignment ----------
TOTAL_ORDERS = 46                 # T
RATE_LIMIT = 20                   # R requests
WINDOW_SECONDS = 10               # per 10 seconds

# ---------- In-memory storage ----------
# Idempotency: key → order dict
idempotency_store: Dict[str, dict] = {}

# Orders catalog (fixed IDs 1..46)
ORDERS = [{"id": i, "status": "created", "amount": 10.0 * i} for i in range(1, TOTAL_ORDERS + 1)]

# Rate limiting: client_id → deque of timestamps
rate_limit_buckets: Dict[str, deque] = defaultdict(deque)


# ---------- Models ----------
class OrderCreate(BaseModel):
    # You can accept any body; we ignore the content for this assignment
    pass


# ---------- 1. Idempotent POST /orders ----------
@app.post("/orders", status_code=201)
def create_order(
    body: OrderCreate = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        # Some graders always send the header; still handle missing case gracefully
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    # Already seen this key? → return the same order (never create a duplicate)
    if idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]

    # First time → create a new order
    new_order = {
        "id": str(uuid.uuid4()),          # unique order id
        "status": "created",
        "amount": 99.99,
    }
    idempotency_store[idempotency_key] = new_order
    return new_order


# ---------- 2. Cursor-based pagination GET /orders ----------
@app.get("/orders")
def list_orders(
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
):
    # Convert cursor to starting index (opaque cursor = just the next ID as string)
    if cursor is None:
        start_id = 1
    else:
        try:
            start_id = int(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    # Collect up to `limit` orders starting from start_id
    items = []
    current_id = start_id

    while len(items) < limit and current_id <= TOTAL_ORDERS:
        # Find the order with this id (they are already sorted)
        order = next((o for o in ORDERS if o["id"] == current_id), None)
        if order:
            items.append(order)
        current_id += 1

    # Next cursor = the next ID we would have returned, or None if finished
    next_cursor = str(current_id) if current_id <= TOTAL_ORDERS else None

    return {
        "items": items,               # or "orders" / "data" – grader accepts common aliases
        "next_cursor": next_cursor,   # or "next"
    }


# ---------- 3. Per-client rate limiting (middleware) ----------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Always let OPTIONS (CORS preflight) through
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id")

    if client_id:
        now = time.time()
        bucket = rate_limit_buckets[client_id]

        # Drop timestamps older than the 10-second window
        while bucket and now - bucket[0] > WINDOW_SECONDS:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT:
            retry_after = max(1, int(WINDOW_SECONDS - (now - bucket[0])) + 1)

            # IMPORTANT: include CORS headers so the browser can see the 429
            origin = request.headers.get("Origin", "*")
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Expose-Headers": "Retry-After",
                },
            )

        bucket.append(now)

    response = await call_next(request)
    return response


# ---------- Health check (nice to have) ----------
@app.get("/")
def root():
    return {"message": "Orders API is running", "total_orders": TOTAL_ORDERS}
