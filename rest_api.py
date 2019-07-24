from aiohttp import web
from loguru import logger

routes = web.RouteTableDef()


@routes.post("/healthcheck")
async def health_check(request):
    return web.HTTPOk()


def start_healthcheck():
    app = web.Application()
    app.add_routes(routes)
    logger.info("Healthcheck started")
    web.run_app(app, port=1337)
