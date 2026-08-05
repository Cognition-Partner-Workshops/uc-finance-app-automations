"""
FastAPI application entry point with Socket.io mount.
This is the main application module that wires everything together.
"""

import logging
import os

import sentry_sdk
import socketio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.middleware import TenantMiddleware
from app.routes import accounts, trades, positions, people, reference_data, analytics
from app.services.trade_processor import set_socketio_server

# =============================================================================
# Sentry SDK Initialization (must happen before app is created)
# =============================================================================
# Load environment variables from a local .env file if present (localhost demo).
load_dotenv()
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=1.0,
        enable_logs=True,
    )

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Socket.io Server
# =============================================================================

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=SOCKETIO_CORS_ALLOWED,
    logger=DEBUG,
    engineio_logger=False,
)


@sio.event
async def connect(sid, environ):
    logger.info("Socket.io client connected: %s", sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket.io client disconnected: %s", sid)


@sio.event
async def subscribe(sid, data):
    """Handle room subscription requests from the frontend."""
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.enter_room(sid, room)
        logger.info("Client %s subscribed to room: %s", sid, room)


@sio.event
async def unsubscribe(sid, data):
    """Handle room unsubscription requests."""
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.leave_room(sid, room)
        logger.info("Client %s unsubscribed from room: %s", sid, room)


# Set the Socket.io server reference in trade_processor
set_socketio_server(sio)

# =============================================================================
# FastAPI Application
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # Tenant middleware
    app.add_middleware(TenantMiddleware)

    # Include routers
    app.include_router(accounts.router, tags=["Accounts"])
    app.include_router(trades.router, tags=["Trades"])
    app.include_router(positions.router, tags=["Positions"])
    app.include_router(people.router, tags=["People"])
    app.include_router(reference_data.router, tags=["Reference Data"])
    app.include_router(analytics.router, tags=["Analytics"])

    @app.get("/")
    def root():
        return {
            "service": APP_TITLE,
            "version": APP_VERSION,
            "status": "running",
        }

    @app.get("/health")
    def health():
        return {"status": "UP"}

    @app.get("/sentry-debug")
    async def trigger_error():
        """Report a demo error to Sentry and return a handled 500 response."""
        try:
            division_by_zero = 1 / 0  # noqa: F841
        except ZeroDivisionError as exc:
            sentry_sdk.capture_exception(exc)
            raise HTTPException(
                status_code=500,
                detail="Sentry demo error triggered",
            ) from exc

    logger.info("FastAPI application created with all routes")
    return app


# Create the app instance
app = create_app()

# Mount Socket.io on the ASGI app
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
