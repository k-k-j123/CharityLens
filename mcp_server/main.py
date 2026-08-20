from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp_server.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("CharityLens MCP Server starting...")
    yield
    print("CharityLens MCP Server shutting down...")


app = FastAPI(
    title="CharityLens MCP Server",
    description="AI-Powered NGO Trust & Transparency Platform - Tool Layer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "CharityLens MCP Server",
        "version": "0.1.0",
        "docs": "/docs",
        "tools_endpoint": "/tools",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
