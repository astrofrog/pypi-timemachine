import logging
from contextlib import asynccontextmanager
import dataclasses
from datetime import datetime
import socket
import sys
import typing

import click
import fastapi
import httpx
from simple_repository.components.core import RepositoryContainer, SimpleRepository
from simple_repository.components.http import HttpRepository
from simple_repository_server.routers import simple
from simple_repository import model
import uvicorn


if sys.version_info >= (3, 12):
    from typing import override
else:

    def override(fn):
        return fn


MAIN_PYPI = "https://pypi.org/simple/"


def parse_iso(dt) -> datetime:
    try:
        return datetime.strptime(dt, "%Y-%m-%d")
    except ValueError:
        if dt.endswith("Z"):
            dt = dt[:-1]
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")


def create_app(repo: SimpleRepository, cutoff: datetime) -> fastapi.FastAPI:
    @asynccontextmanager
    async def lifespan(app: fastapi.FastAPI) -> typing.AsyncIterator[None]:
        def repo_factory(cutoff_date: str) -> SimpleRepository:
            try:
                CUTOFF = parse_iso(cutoff_date)
            except Exception:
                raise fastapi.HTTPException(
                    status_code=400,
                    detail="Date string does not conform to %Y-%m-%d or %Y-%m-%dT%H:%M:%SZ",
                )

            return DateFilteredReleases(
                repo,
                cutoff_date=CUTOFF,
            )

        async with httpx.AsyncClient() as http_client:
            app.include_router(
                simple.build_router(
                    repo,
                    http_client=http_client,
                    prefix="/snapshot/{cutoff_date}/",
                    repo_factory=repo_factory,
                )
            )

            @app.get("/")
            @app.get("/{project_name}/")
            def redirect_to_simple(request: fastapi.Request):
                # Allow accessing without specifying the snapshot date, but have this redirect.
                # We don't make it permanent, because we may restart the server with a new "default cutoff date".
                # This also gives us backwards compatibility for when we only supported a single cut-off date.
                return fastapi.responses.RedirectResponse(
                    f"/snapshot/{cutoff.strftime('%Y-%m-%dT%H:%M:%SZ')}{request.url.path}",
                    status_code=302,
                )

            yield

    app = fastapi.FastAPI(
        openapi_url=None,  # Disables automatic OpenAPI documentation (Swagger & Redoc)
        lifespan=lifespan,
    )
    return app


class DateFilteredReleases(RepositoryContainer):
    """
    A component used to remove released projects from the source
    repository if they were released after the configured date.

    This component can be used only if the source repository exposes the upload
    date according to PEP-700: https://peps.python.org/pep-0700/.

    """

    def __init__(
        self,
        source: SimpleRepository,
        cutoff_date: datetime,
    ) -> None:
        self._cutoff_date = cutoff_date
        super().__init__(source)

    @override
    async def get_project_page(
        self,
        project_name: str,
        *,
        request_context: model.RequestContext | None = None,
    ) -> model.ProjectDetail:
        project_page = await super().get_project_page(
            project_name,
            request_context=request_context,
        )

        return self._exclude_recent_distributions(
            project_page=project_page,
        )

    def _exclude_recent_distributions(
        self,
        project_page: model.ProjectDetail,
    ) -> model.ProjectDetail:
        filtered_files = tuple(
            file
            for file in project_page.files
            if not file.upload_time or (file.upload_time <= self._cutoff_date)
        )
        return dataclasses.replace(project_page, files=filtered_files)


@click.command()
@click.argument("cutoff_date")
@click.option("--port", default=None)
@click.option("--quiet", default=False, is_flag=True)
@click.option("--index-url", default=MAIN_PYPI)
def main(cutoff_date: str | None, port: str | None, quiet: bool, index_url: str):
    CUTOFF = parse_iso(cutoff_date)

    repo = HttpRepository(index_url)

    # TODO: Currently all resources get streamed through our server, so an installation of a big wheel
    #  results in a lot of traffic passing through the timemachine server. The issue for this
    #  can be found at https://github.com/simple-repository/simple-repository-server/issues/15.
    app = create_app(repo, CUTOFF)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    if port is None:
        port = sock.getsockname()[1]
    sock.close()

    if not quiet:
        print(
            f"pypi-timemachine server listening at http://localhost:{port}  (ctrl+c to exit)"
        )
        print(
            f'  Hint: Setting the environment variable PIP_INDEX_URL="http://localhost:{port}" is one way to configure pip to use this timemachine'
        )

    uvicorn.run(app=app, port=int(port), log_level=logging.WARN)
