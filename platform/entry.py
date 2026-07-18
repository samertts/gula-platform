#!/usr/bin/env python3
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="GULA Platform API")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--workers", type=int, default=int(os.getenv("WORKERS", "1")))
    parser.add_argument("--env", default=os.getenv("ENVIRONMENT", "development"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--redis-url", default=os.getenv("REDIS_URL", ""))
    parser.add_argument("--reload", action="store_true", default=os.getenv("RELOAD", "false").lower() == "true")
    args = parser.parse_args()

    config = {
        "environment": args.env,
        "database_url": args.db_url,
        "redis_url": args.redis_url,
        "cors_origins": ["*"],
        "title": "GULA Platform API",
        "version": "1.0.0",
    }

    os.environ["GULA_ENV"] = args.env

    import uvicorn
    uvicorn.run(
        "platform.api.app:create_app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        factory=True,
    )


if __name__ == "__main__":
    main()
