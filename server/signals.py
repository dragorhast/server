from aiohttp import WSCloseCode

from server import logger


async def close_bike_connections(app):
    connections = set(app['bike_connections'])
    if connections:
        logger.info("Closing all open bike connections")
    for ws in set(app['bike_connections']):
        await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')
