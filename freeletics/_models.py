import json
from collections.abc import MutableMapping
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import httpx
import jwt


class BaseToken:
    def __init__(self, token: str) -> None:
        self._token = token
        self._payload = self._get_token_payload(token)

    @classmethod
    def _get_token_payload(cls, token: str) -> Dict[str, Any]:
        return jwt.decode(token, options={"verify_signature": False})

    @property
    def token(self) -> str:
        return self._token

    @property
    def payload(self) -> Dict[str, Any]:
        return self._payload

    @property
    def expires_timestamp(self) -> int:
        return self.payload['exp']

    @property
    def expires_datetime(self) -> datetime:
        return datetime.utcfromtimestamp(self.expires_timestamp).\
            replace(tzinfo=timezone.utc)

    @property
    def expires_in_seconds(self) -> float:
        return (self.expires_datetime - datetime.now(timezone.utc)).\
            total_seconds()

    @property
    def is_expired(self) -> bool:
        return self.expires_in_seconds <= 0

    @property
    def audiences(self) -> List:
        return self.payload['aud']


class IdToken(BaseToken):
    def __init__(self, token, user_id: Optional[int] = None) -> None:
        super().__init__(token)

        assert 'standard' in self.audiences, 'Token is not a valid id token'

        if user_id and user_id != self.user_id:
            raise Exception('user_id does not match id_token user_id')

    @property
    def user_id(self) -> int:
        return self.payload['user_id']


class PaymentToken(BaseToken):
    def __init__(self, token) -> None:
        super().__init__(token)
        assert 'payment_token' in self.audiences, 'Token is not a valid ' \
                                                  'payment token '

    @property
    def payment_status(self) -> List:
        return self.payload['payment']['claims']

    @property
    def user_id(self) -> int:
        return self.payload['payment']['user_id']


class RefreshToken:
    def __init__(self, token: str, user_id: int) -> None:
        self._token = token
        self._user_id = user_id

    @property
    def token(self) -> str:
        return self._token

    @property
    def user_id(self) -> int:
        return self._user_id


class CoreResponseModel(MutableMapping):
    def __init__(self,
                 data: Dict[str, Any],
                 response: httpx.Response,
                 session: Union[httpx.Client, httpx.AsyncClient]) -> None:
        self._data = data
        self._response = response
        self._session = session

    def __getitem__(self, key):
        return self._data[self._keytransform(key)]

    def __setitem__(self, key, value):
        self._data[self._keytransform(key)] = value

    def __delitem__(self, key):
        del self._data[self._keytransform(key)]

    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)

    def _keytransform(self, key):
        return key

    @property
    def response(self) -> httpx.Response:
        return self._response

    @property
    def request(self) -> httpx.Request:
        return self.response.request

    def as_dict(self) -> Dict[str, Any]:
        return self._data

    def as_json(self, **options):
        return json.dumps(self._data,
                          default=lambda o: o.as_dict(),
                          **options)

    @property
    def etag(self):
        if self.response is not None and 'ETag' in self.response.headers:
            return self.response.headers['ETag']

    def update_from_request(self):
        if self.etag is not None and self.request.method == 'GET':
            headers = {
                'If-None-Match': self.etag
            }
            self.request.headers.update(headers)
        r = self._session.send(self.request)
        self._response = r
        if r.status_code != 304:
            self.update(r.json())
        return self
