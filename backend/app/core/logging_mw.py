import json
import logging
import time
import uuid
from fastapi import Request

logger = logging.getLogger("rankforge.access")
logging.basicConfig(level=logging.INFO, format="%(message)s")


async def structured_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    t0 = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    log_entry = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": latency_ms,
        "cache": response.headers.get("X-Cache", "BYPASS"),
    }
    logger.info(json.dumps(log_entry))
    return response
