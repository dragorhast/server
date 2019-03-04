"""
A custom Gunicorn worker to support ``aiomonitor``
"""

import asyncio
import os

import aiomonitor
from aiohttp import GunicornUVLoopWebWorker, web
from aiohttp.web_app import Application

from server.monitor import Tap2GoMonitor


class GunicornUVLoopAiomonitorWebWorker(GunicornUVLoopWebWorker):
    """
    Extends the GunicornUVLoopWebWorker to also start aiomonitor.
    """

    async def _run(self) -> None:
        if isinstance(self.wsgi, Application):
            app = self.wsgi
        elif asyncio.iscoroutinefunction(self.wsgi):
            app = await self.wsgi()
        else:
            raise RuntimeError("wsgi app should be either Application or "
                               "async function returning Application, got {}"
                               .format(self.wsgi))
        access_log = self.log.access_log if self.cfg.accesslog else None
        runner = web.AppRunner(app,
                               logger=self.log,
                               keepalive_timeout=self.cfg.keepalive,
                               access_log=access_log,
                               access_log_format=self._get_valid_log_format(
                                   self.cfg.access_log_format))
        await runner.setup()

        aiomonitor.start_monitor(loop=self.loop, locals={"app": app}, monitor=Tap2GoMonitor)

        ctx = self._create_ssl_context(self.cfg) if self.cfg.is_ssl else None

        runner = runner
        assert runner is not None
        server = runner.server
        assert server is not None
        for sock in self.sockets:
            site = web.SockSite(
                runner, sock, ssl_context=ctx,
                shutdown_timeout=self.cfg.graceful_timeout / 100 * 95)
            await site.start()

        # If our parent changed then we shut down.
        pid = os.getpid()
        try:
            while self.alive:  # type: ignore
                self.notify()

                cnt = server.requests_count
                if self.cfg.max_requests and cnt > self.cfg.max_requests:
                    self.alive = False
                    self.log.info("Max requests, shutting down: %s", self)

                elif pid == os.getpid() and self.ppid != os.getppid():
                    self.alive = False
                    self.log.info("Parent changed, shutting down: %s", self)
                else:
                    await self._wait_next_notify()
        except BaseException:
            pass

        await runner.cleanup()
