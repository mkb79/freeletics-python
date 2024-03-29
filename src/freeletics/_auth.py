import asyncio
import logging
import threading
from typing import AsyncGenerator, Generator, Optional, Union

import httpx

from ._api import ApiRequestBuilder
from ._models import IdToken, RefreshToken


logger = logging.getLogger(__name__)


class FreeleticsAuth(httpx.Auth):
    def __init__(
        self,
        id_token: Optional[IdToken],
        refresh_token: Optional[RefreshToken],
        session: Union[httpx.Client, httpx.AsyncClient],
        api_request_builder: ApiRequestBuilder,
    ) -> None:
        self._id_token = id_token
        self._refresh_token = refresh_token
        self._session = session
        self._api_request_builder = api_request_builder
        self._sync_lock = threading.RLock()
        self._async_lock = asyncio.Lock()

    @property
    def id_token(self) -> Optional[IdToken]:
        return self._id_token

    @id_token.setter
    def id_token(self, id_token: IdToken) -> None:
        if (
            self.refresh_token is not None
            and id_token.user_id != self.refresh_token.user_id
        ):
            raise Exception("user_id for id_token and refresh_token are not " "equal")
        self._id_token = id_token

    @property
    def refresh_token(self) -> Optional[RefreshToken]:
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, refresh_token: RefreshToken) -> None:
        if self.refresh_token is not None:
            raise Exception("Refresh Token can only be set once.")

        if self.id_token is not None and refresh_token.user_id != self.id_token.user_id:
            raise Exception("user_id for id_token and refresh_token are not " "equal")

        self._refresh_token = refresh_token

    def _set_auth_header(self, request) -> None:
        request.headers["Authorization"] = "Bearer " + self.id_token.token

    def _set_token_from_response(self, response: httpx.Response) -> None:
        if response.status_code != httpx.codes.CREATED:
            if response.status_code == 404:
                raise Exception(
                    "No internet connection or session expired. "
                    "Please try to login again."
                )
            else:
                response.raise_for_status()

        data = response.json()
        id_token = IdToken(data["auth"]["id_token"])
        self.id_token = id_token
        logger.info("set new id_token")

    def _build_update_id_token_request(self) -> httpx.Request:
        return self._api_request_builder.update_id_token(
            refresh_token=self.refresh_token.token, user_id=self.refresh_token.user_id
        )

    def sync_auth_flow(self, request) -> Generator[httpx.Request, httpx.Response, None]:
        with self._sync_lock:
            if self.id_token is None or self.id_token.expires_in_seconds < 20:
                if self.refresh_token is None:
                    raise Exception("id_token and refresh_token not set")
                self.sync_update_id_token()

        self._set_auth_header(request)
        yield request

    async def async_auth_flow(
        self, request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        async with self._async_lock:
            if self.id_token is None or self.id_token.expires_in_seconds < 20:
                if self.refresh_token is None:
                    raise Exception("id_token and refresh_token not set")
                await self.async_update_id_token()

        self._set_auth_header(request)
        yield request

    def sync_update_id_token(self) -> None:
        logger.info("Requesting new id_token")

        if not isinstance(self._session, httpx.Client):
            raise Exception("Client is not an Client")

        request = self._build_update_id_token_request()
        response = self._session.send(request, auth=None)
        self._set_token_from_response(response)

    async def async_update_id_token(self) -> None:
        logger.info("Requesting new id_token")

        if not isinstance(self._session, httpx.AsyncClient):
            raise Exception("Client is not an AsyncClient")

        request = self._build_update_id_token_request()
        response = await self._session.send(request, auth=None)
        self._set_token_from_response(response)
