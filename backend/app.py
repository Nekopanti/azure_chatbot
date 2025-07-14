import uvicorn
import os
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from src.common.posm_service_azure import NaturalLanguageQASystem
from src.common.logger import get_logger

logger = get_logger("app")


# Get SECRET_KEY from environment variables
SECRET_KEY = os.getenv("FASTAPI_SECRET_KEY")
if not SECRET_KEY:
    logger.error("FASTAPI_SECRET_KEY environment variable is missing!")
    raise RuntimeError("Missing FASTAPI_SECRET_KEY")

# Get ALLOWED_ORIGINS from environment variables
origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
if not allowed_origins:
    logger.warn("ALLOWED_ORIGINS is empty! CORS will be very restrictive")

# Get ALLOWED_IPS from environment variables
raw_ips = os.getenv("ALLOWED_IPS", "")
allowed_ips = [ip.strip() for ip in raw_ips.split(",") if ip.strip()]
if not allowed_ips:
    logger.warn("ALLOWED_IPS is empty! All IPs will be allowed (no restriction).")

# Get environment from environment variables
ENV = os.getenv("FASTAPI_ENV")

# Instantiate the FastAPI app
app = FastAPI()

# CORS Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


def get_real_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host


# Get real user IP (supports local and X-Forwarded-For)
@app.middleware("http")
async def ip_whitelist_middleware(request: Request, call_next):
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host

    if allowed_ips and client_ip not in allowed_ips:
        return JSONResponse(
            status_code=403,
            content={"detail": f"Forbidden: IP {client_ip} not allowed"},
        )

    return await call_next(request)


# CORS Settings
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# Initialize the service class
posm_service = NaturalLanguageQASystem(
    search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello", response_class=JSONResponse)
def hello():
    return "Hello, FastAPI!"


@app.get("/ask_question", response_class=JSONResponse)
async def ask_question(question: str = Query(...)) -> JSONResponse:
    try:
        if not question or not question.strip():
            raise HTTPException(
                status_code=400, detail="Query parameter 'question' is required."
            )

        cleaned_question = question.strip().strip('"')

        logger.info(f"Received question: {cleaned_question}")

        result = posm_service.ask_question(cleaned_question)

        return JSONResponse(status_code=200, content={"status": "ok", "result": result})

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error("Error occurred while processing question")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/generate_title", response_class=JSONResponse)
async def generate_title(summary: str = Query(...)) -> JSONResponse:
    try:
        if not summary or not summary.strip():
            raise HTTPException(
                status_code=400, detail="Parameter 'summary' cannot be empty."
            )

        cleaned_summary = summary.strip().strip('"')

        logger.info(f"Received summary: {cleaned_summary}")

        title = posm_service.generate_title(cleaned_summary)

        return JSONResponse(status_code=200, content={"status": "ok", "title": title})

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error("Error occurred while generating title")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate title: {str(e)}"
        )


@app.get("/clear_session", response_class=JSONResponse)
async def clear_session(request: Request):
    if hasattr(request, "session"):
        request.session.clear()
    return JSONResponse(content={"message": "Session cleared"})


@app.get("/health_check")
async def health_check():
    return JSONResponse(content={"status": "ok"})


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
