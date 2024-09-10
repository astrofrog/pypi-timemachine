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
    override = lambda fn: fn


MAIN_PYPI = 'https://pypi.org/simple/'


def parse_iso(dt) -> datetime:
    try:
        return datetime.strptime(dt, '%Y-%m-%d')
    except:
        return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')


def create_app(repo: SimpleRepository) -> fastapi.FastAPI:
    @asynccontextmanager
    async def lifespan(app: fastapi.FastAPI) -> typing.AsyncIterator[None]:
        async with httpx.AsyncClient() as http_client:
            app.include_router(simple.build_router(repo, http_client), prefix="")
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
        request_context: model.RequestContext = model.RequestContext.DEFAULT,
    ) -> model.ProjectDetail:
        project_page = await super().get_project_page(
            project_name,
            request_context=request_context,
        )

        return self._exclude_recent_distributions(
            project_page=project_page,
            now=datetime.now(),
        )

    def _exclude_recent_distributions(
        self,
        project_page: model.ProjectDetail,
        now: datetime,
    ) -> model.ProjectDetail:
        filtered_files = tuple(
            file for file in project_page.files
            if not file.upload_time or
            (file.upload_time <= self._cutoff_date)
        )
        return dataclasses.replace(project_page, files=filtered_files)


@click.command()
@click.argument('cutoff_date')
@click.option('--port', default=None)
@click.option('--quiet', default=False, is_flag=True)
def main(cutoff_date, port, quiet):

    CUTOFF = parse_iso(cutoff_date)

    repo = DateFilteredReleases(
        HttpRepository(MAIN_PYPI),
        cutoff_date=CUTOFF,
    )

    app = create_app(repo)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    if port is None:
        port = sock.getsockname()[1]
    sock.close()

    if not quiet:
        print(f'Starting pypi-timemachine server at http://localhost:{port}')

    uvicorn.run(app=app, port=int(port))
