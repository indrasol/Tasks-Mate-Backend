import logging

def pytest_configure(config):
    # Lower log verbosity for noisy modules
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("h2").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase_py").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # if used
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)


    logging.getLogger("hpack").disabled = True
    logging.getLogger("h2").disabled = True
    logging.getLogger("httpcore").disabled = True
    logging.getLogger("httpx").disabled = True
