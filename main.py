import asyncio
import uvicorn
from webserver.server import app

async def start_server():
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
        timeout_keep_alive=0,
        access_log=True,
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    server_task = asyncio.create_task(start_server())
    await asyncio.gather(server_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down services...")
    except Exception as e:
        print(f"Error: {e}")
