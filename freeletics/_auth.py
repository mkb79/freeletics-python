import asyncio
import logging
import threading

from typing import Optional, Union

import httpx

from ._models import IdToken, RefreshToken

logger = logging.getLogger(__name__)


class FreeleticsAuth(httpx.Auth):
    def __init__(self,
                 id_token: Optional[IdToken],
                 refresh_token: Optional[RefreshToken],
                 session: Union[httpx.Client, httpx.AsyncClient]) -> None:

        self._id_token = id_token
        self._refresh_token = refresh_token
        self._session = session
        self._sync_lock = threading.RLock()
        self._async_lock = asyncio.Lock()

    @property
    def id_token(self) -> Optional[IdToken]:
        return self._id_token

    @id_token.setter
    def id_token(self, id_token: IdToken) -> None:
        if self.refresh_token is not None and \
                id_token.user_id != self.refresh_token.user_id:
            raise Exception('user_id for id_token and refresh_token are not '
                            'equal')
        self._id_token = id_token

    @property
    def refresh_token(self) -> Optional[RefreshToken]:
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, refresh_token: RefreshToken) -> None:
        if self._refresh_token is not None:
            raise Exception('Refresh Token can only be set once.')

        if self.id_token is not None and \
                refresh_token.user_id != self.id_token.user_id:
            raise Exception('user_id for id_token and refresh_token are not '
                            'equal')

        self._refresh_token = refresh_token

    def _set_auth_header(self, request) -> None:
        request.headers['Authorization'] = 'Bearer ' + self.id_token.token

    def sync_auth_flow(self, request):
        with self._sync_lock:
            if self.id_token is None:
                if self.refresh_token is None:
                    raise Exception('id_token and refresh_token not set')
                else:
                    self.sync_update_id_token()
            elif self.id_token.expires_in_seconds < 20:
                self.sync_update_id_token()

        self._set_auth_header(request)
        yield request

    async def async_auth_flow(self, request):
        async with self._async_lock:
            if self.id_token is None:
                if self.refresh_token is None:
                    raise Exception('id_token and refresh_token not set')
                else:
                    await self.async_update_id_token()
            elif self.id_token.expires_in_seconds < 20:
                await self.async_update_id_token()

        self._set_auth_header(request)
        yield request

    def _send_update_id_token_request(self) -> httpx.Response:
        data = {
          "user_id": self.refresh_token.user_id,
          "refresh_token": self.refresh_token.token
        }
        return self._session.post('/user/v1/auth/refresh', json=data, auth=None)

    def _set_token_from_response(self, response: httpx.Response) -> None:
        data = response.json()
        id_token = IdToken(data['auth']['id_token'])
        self.id_token = id_token

    def sync_update_id_token(self):
        logger.info('Requesting new id_token')

        response = self._send_update_id_token_request()
        response.raise_for_status()
        self._set_token_from_response(response)
        logger.info('id_token refreshed')

    async def async_update_id_token(self):
        logger.info('Requesting new id_token')

        response = await self._send_update_id_token_request()
        response.raise_for_status()
        self._set_token_from_response(response)
        logger.info('id_token refreshed')
