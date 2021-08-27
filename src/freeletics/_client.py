import json
import logging
from typing import Any, Dict, Optional, Union

import httpx

from ._api import ApiRequestBuilder
from ._auth import FreeleticsAuth
from ._models import (AsyncCoreResponseModel,
                      CoreResponseModel,
                      IdToken,
                      RefreshToken)

logger = logging.getLogger(__name__)


class FreeleticsClient:
    _SESSION = httpx.Client

    def __init__(self) -> None:
        self._session = self._SESSION()
        self._api_request_builder = ApiRequestBuilder(self._session)
        self._session.auth = FreeleticsAuth(
            id_token=None,
            refresh_token=None,
            session=self._session,
            api_request_builder=self._api_request_builder)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self) -> None:
        self._session.close()

    @classmethod
    def from_credentials(cls, id_token: Optional[str] = None,
                         refresh_token: Optional[str] = None,
                         user_id: Optional[int] = None,
                         detect_user_id: bool = False
                         ) -> Union['FreeleticsClient',
                                    'AsyncFreeleticsClient']:
        if id_token is not None:
            id_token = IdToken(id_token, user_id)

        if refresh_token is not None:
            if user_id is None:
                if not detect_user_id:
                    raise Exception('refresh token without user_id provided')
                if detect_user_id and id_token is None:
                    raise Exception('Can not detect user id, no id token '
                                    'provided')

            user_id = user_id or id_token.user_id
            refresh_token = RefreshToken(refresh_token, user_id)

        new_cls = cls()
        new_cls._session.auth.refresh_token = refresh_token
        new_cls._session.auth.id_token = id_token
        return new_cls

    def get_credentials(self) -> Dict[str, Any]:
        return {
            'id_token': self._session.auth.id_token.token,
            'refresh_token': self._session.auth.refresh_token.token,
            'user_id': self._session.auth.refresh_token.user_id
        }

    @property
    def is_authenticated(self) -> bool:
        auth = self._session.auth
        if auth is not None:
            if auth.refresh_token:
                return True
            if auth.id_token and not auth.id_token.is_expired:
                return True
        return False

    @property
    def user_id(self) -> Union[str, int]:
        if self._session.auth.id_token is not None:
            return self._session.auth.id_token.user_id
        else:
            return self._session.auth.refresh_token.user_id

    def request(self, method, url, **kwargs) -> CoreResponseModel:
        request = self._api_request_builder.request(method, url, **kwargs)
        return self.send(request)

    def send(self, request, **kwargs) -> CoreResponseModel:
        r = self._session.send(request, **kwargs)
        r.raise_for_status()
        try:
            return CoreResponseModel(
                data=r.json(),
                response=r,
                session=self._session)
        except json.JSONDecodeError:
            return CoreResponseModel(
                data={},
                response=r,
                session=self._session)

    def _set_auth_from_login_response(self, response) -> None:
        data = response.as_dict()
        user_id = data['user']['fl_uid']
        auth = data['authentication']
        id_token = IdToken(token=auth['id_token'], user_id=user_id)
        refresh_token = RefreshToken(token=auth['refresh_token'],
                                     user_id=user_id)

        self._session.auth.refresh_token = refresh_token
        self._session.auth.id_token = id_token

    def login(self, username, password) -> CoreResponseModel:
        request = self._api_request_builder.login_user(username=username,
                                                       password=password)
        response = self.send(request, auth=None)
        self._set_auth_from_login_response(response)

        logger.info('Logged in as ' + username)
        return response

    def logout(self) -> Union[AsyncCoreResponseModel, CoreResponseModel]:
        request = self._api_request_builder.logout_user(
            refresh_token=self._session.auth.refresh_token.token,
            user_id=self._session.auth.refresh_token.user_id)
        response = self.send(request)
        self._session.auth._refresh_token = None
        self._session.auth._id_token = None
        return response

    def get_calendar(self, payment_token) -> Union[AsyncCoreResponseModel,
                                                   CoreResponseModel]:
        request = self._api_request_builder.get_calendar(payment_token)
        return self.send(request)

    def get_calendar_by_date(self,
                             date: str,
                             payment_token: str,
                             distance_unit_system: str = 'metric',
                             weight_unit_system: str = 'metric',
                             skill_paths_enabled: str = 'true') -> Union[
            AsyncCoreResponseModel, CoreResponseModel]:
        request = self._api_request_builder.get_calendar_by_date(
            date=date,
            payment_token=payment_token,
            distance_unit_system=distance_unit_system,
            weight_unit_system=weight_unit_system,
            skill_paths_enabled=skill_paths_enabled)
        return self.send(request)

    def get_coach_exercises(self) -> Union[AsyncCoreResponseModel,
                                           CoreResponseModel]:
        request = self._api_request_builder.get_coach_exercises()
        return self.send(request)

    def get_coach_settings(self) -> Union[AsyncCoreResponseModel,
                                          CoreResponseModel]:
        request = self._api_request_builder.get_coach_settings()
        return self.send(request)

    def get_coach_workouts_god(self) -> Union[AsyncCoreResponseModel,
                                              CoreResponseModel]:
        request = self._api_request_builder.get_coach_workouts(type_='god')
        return self.send(request)

    def get_coach_workouts_exercise(self) -> Union[AsyncCoreResponseModel,
                                                   CoreResponseModel]:
        request = self._api_request_builder.get_coach_workouts(
            type_='exercise_workout')
        return self.send(request)

    def get_coach_workouts_run(self) -> Union[AsyncCoreResponseModel,
                                              CoreResponseModel]:
        request = self._api_request_builder.get_coach_workouts(type_='run')
        return self.send(request)

    def get_coach_workouts_cooldown(self) -> Union[AsyncCoreResponseModel,
                                                   CoreResponseModel]:
        request = self._api_request_builder.get_coach_workouts(
            type_='cooldown')
        return self.send(request)

    def get_coach_workouts_warmup(self) -> Union[AsyncCoreResponseModel,
                                                 CoreResponseModel]:
        request = self._api_request_builder.get_coach_workouts(type_='warmup')
        return self.send(request)

    def get_messsging_profile(self) -> Union[AsyncCoreResponseModel,
                                             CoreResponseModel]:
        request = self._api_request_builder.get_messsging_profile()
        return self.send(request)

    def get_payment_claims(self,
                           supported_brand_types: Optional[str] = None) -> \
            Union[AsyncCoreResponseModel, CoreResponseModel]:
        request = self._api_request_builder.get_payment_claims(
            supported_brand_types)
        return self.send(request)

    def get_payment_training_coach_by_userid(self, user_id: Optional[
        Union[str, int]] = None) -> Union[AsyncCoreResponseModel,
                                          CoreResponseModel]:
        user_id = user_id or self.user_id
        request = self._api_request_builder.\
            get_payment_training_coach_by_userid(user_id)
        return self.send(request)

    def get_performed_activities_by_id(self, activity_id: Union[str, int]) -> \
            Union[AsyncCoreResponseModel, CoreResponseModel]:
        request = self._api_request_builder.get_performed_activities_by_id(
            activity_id)
        return self.send(request)

    def get_planned_activities_by_id(self, activity_id: Union[str, int]) -> \
            Union[AsyncCoreResponseModel, CoreResponseModel]:
        request = self._api_request_builder.get_planned_activities_by_id(
            activity_id)
        return self.send(request)

    def get_social_feeds(self) -> Union[AsyncCoreResponseModel,
                                        CoreResponseModel]:
        request = self._api_request_builder.get_social_feeds()
        return self.send(request)

    def get_status_bodyweight_app(self) -> Union[AsyncCoreResponseModel,
                                                 CoreResponseModel]:
        request = self._api_request_builder.get_status_bodyweight_app()
        return self.send(request)

    def get_user_activities_by_id(self,
                                  user_id: Optional[Union[str, int]] = None,
                                  page: Optional[Union[str, int]] = None) -> \
            Union[AsyncCoreResponseModel, CoreResponseModel]:
        user_id = user_id or self.user_id
        request = self._api_request_builder.get_user_activities_by_id(
            user_id=user_id, page=page)
        return self.send(request)

    def get_user_profile(self) -> Union[AsyncCoreResponseModel,
                                        CoreResponseModel]:
        request = self._api_request_builder.get_user_profile()
        return self.send(request)

    def get_user_status_general(self) -> Union[AsyncCoreResponseModel,
                                               CoreResponseModel]:
        request = self._api_request_builder.get_user_status_general()
        return self.send(request)


class AsyncFreeleticsClient(FreeleticsClient):
    _SESSION = httpx.AsyncClient

    def __enter__(self):
        raise NotImplementedError('Please use async with statement instead')

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def close(self) -> None:
        await self._session.aclose()

    async def request(self, method, url, **kwargs) -> AsyncCoreResponseModel:
        request = self._api_request_builder.request(method, url, **kwargs)
        return await self.send(request)

    async def send(self, request, **kwargs) -> AsyncCoreResponseModel:
        r = await self._session.send(request, **kwargs)
        r.raise_for_status()
        try:
            return AsyncCoreResponseModel(
                data=r.json(),
                response=r,
                session=self._session)
        except json.JSONDecodeError:
            return AsyncCoreResponseModel(
                data={},
                response=r,
                session=self._session)

    async def login(self, username, password) -> AsyncCoreResponseModel:
        request = self._api_request_builder.login_user(username=username,
                                                       password=password)
        response = await self.send(request, auth=None)
        self._set_auth_from_login_response(response)

        logger.info('Logged in as ' + username)
        return response
