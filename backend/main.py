from contextlib import asynccontextmanager
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import CORS_ORIGINS, DATA_DIR
from .logging_config import configure_logging
from .routers import admin_knowledge_router, conditions_router, compare_router, content_router, history_router, nodes_router, notifications_router, reports_router, score_router, standards_router
from .services import data_loader
from .services.conditions_store import init_conditions_store
from .services.comparison_report_store import init_comparison_report_store
from .services.history_store import init_history_store
from .services.knowledge_store import init_knowledge_store
from .services.metrics import metrics
from .services.notification_store import create_notification, init_notification_store
from .services.standards_link_store import init_standards_link_store

configure_logging()
logger = logging.getLogger("tunnel.api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    data = data_loader.load_data()
    init_conditions_store()
    init_comparison_report_store()
    init_history_store()
    init_knowledge_store()
    init_notification_store()
    init_standards_link_store()
    logger.info(
        "Backend startup context loaded",
        extra={
            "event": "startup_context",
            "data_dir": str(DATA_DIR),
            "cors_origins": CORS_ORIGINS,
            "row_counts": data_loader.data_row_counts(data),
        },
    )
    yield


app = FastAPI(title="Tunnel Smart Advisor API", version="1.0.0", lifespan=lifespan)

@app.middleware("http")
async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics.record_exception(latency_ms)
        logger.exception(
            "Unhandled request exception",
            extra={
                "event": "request_exception",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "latency_ms": latency_ms,
            },
        )
        try:
            create_notification(
                "system",
                "시스템 오류 감지",
                f"{request.method} {request.url.path} 요청 처리 중 오류가 발생했습니다. request_id={request_id}, error={type(exc).__name__}",
                is_important=True,
            )
        except Exception:
            logger.exception(
                "Failed to persist system error notification",
                extra={"event": "notification_persist_failure", "request_id": request_id},
            )
        raise
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    metrics.record_request(latency_ms, response.status_code)
    response.headers["X-Request-ID"] = request_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nodes_router)
app.include_router(admin_knowledge_router)
app.include_router(score_router)
app.include_router(conditions_router)
app.include_router(compare_router)
app.include_router(content_router)
app.include_router(history_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(standards_router)


@app.post("/admin/cache/reload", tags=["admin"])
def reload_ontology_cache():
    _data, counts = data_loader.reload_data()
    create_notification(
        "data",
        "데이터 캐시 갱신 완료",
        f"온톨로지 CSV 캐시가 갱신되었습니다. 위험 {counts.get('risk', 0)}건, 관계 {counts.get('rels', 0)}건을 로드했습니다.",
    )
    return {"status": "reloaded", "data": counts}

@app.get("/")
def root():
    return {
        "name": "Tunnel Smart Advisor API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    try:
        data = data_loader.load_data()
    except Exception:
        metrics.record_data_load_failure()
        raise
    return {
        "status": "ready",
        "data": data_loader.data_row_counts(data),
    }


@app.get("/metrics", tags=["operations"])
def metrics_snapshot():
    return metrics.snapshot()
