"""
Inspired from http://topu.ch/it/reverse-engineering-des-freeletics-apis/
"""


import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from . import _constants as cs
from ._auth import FreeleticsAuth, IdToken, RefreshToken


logger = logging.getLogger(__name__)


class BaseClient:

    _SESSION = None

    def __init__(self,
                 id_token: Optional[str] = None,
                 refresh_token: Optional[str] = None,
                 user_id: Optional[int] = None,
                 detect_user_id: bool = False):

        if id_token is not None:
            id_token = IdToken(id_token, user_id)

        if refresh_token is not None:
            if user_id is None:
                if not detect_user_id:
                    raise Exception('refresh token without user_id provided')
                if detect_user_id and id_token is None:
                    raise Exception('Can not detect user id, no id token provided')

            user_id = user_id or id_token.user_id
            refresh_token = RefreshToken(refresh_token, user_id)            

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8'
        }

        self._session = self._SESSION(headers=headers, base_url=cs.BASE_URL)

        self._session.auth = FreeleticsAuth(
            id_token=id_token,
            refresh_token=refresh_token,
            session=self._session)

    @property
    def is_authenticated(self):
        auth = self._session.auth
        if auth is not None:
            if auth.refresh_token:
                return True
            if auth.id_token and not auth.id_token.is_expired:
                return True
        return False

    def request(self, method, url, **kwargs):
        raise NotImplementedError

    def login(self, username, password):
        """
        Does not work at this moment. Server raises a HTTP Status Code 426.
        Login request have to be signed using a `X-Authorization` and 
        `X-Authorization-Timestamp` header. 
        Have to find out how X-Authorization token is created.
        Update: Have found out that the request body is part of the signing
                process. Using signing headers from a fresh login with the
                iOS Freeletics App let me login with my Client, if the request
                body is formed (remove whitespaces) like the iOS App does.
        """
        print('This method doesnt work at this time')
        url = '/user/v2/password/authentication'

        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        now_ts = round(now.timestamp() * 1000)
        headers = {
            'X-Authorization': 'None',
            'X-Authorization-Timestamp': str(now_ts),
            'Content-Type': 'application/json'
        }

        data = {
            "authentication": {
                "email": username,
                "password": password
            }
        }
        data = json.dumps(data, separators=(',', ':'))
        return self.request("POST", url, data=data, headers=headers, auth=None)

    def profile(self):
        url = '/v4/profile'
        return self.request('GET', url)

    def payment(self):
        url = '/payment/v3/claims'
        params = {
            'supported_brand_types': 'bodyweight-coach,nutrition-coach,gym-coach,running-coach,training-coach,training-nutrition-coach,mind-coach,mind-training-nutrition-coach'
        }
        return self.request('GET', url, params=params)

    def payment_trainig_coach(self, user_id):
        url = f'/payment/v1/claims/training-coach/{user_id}'
        return self.request('GET', url)

    def status_app(self):
        url = '/user/v1/status/bodyweight/'
        return self.request('GET', url)

    def messaging(self):
        url = '/messaging/v1/profile'
        return self.request('GET', url)

    def coach_settings(self):
        url = '/v5/coach/settings'
        return self.request('GET', url)

    def coach_exercise(self):
        url = '/v5/coach/exercises'
        return self.request('GET', url)

    def status_general(self):
        url = '/user/v1/status/general/'
        return self.request('GET', url)

    def coach_workouts_god(self):
        url = '/v5/coach/workouts'
        params = {
            'type': 'god'
        }
        return self.request('GET', url, params=params)

    def coach_workouts_exercise(self):
        url = '/v5/coach/workouts'
        params = {
            'type': 'exercise_workout'
        }
        return self.request('GET', url, params=params)

    def coach_workouts_run(self):
        url = '/v5/coach/workouts'
        params = {
            'type': 'run'
        }
        return self.request('GET', url, params=params)

    def coach_workouts_cooldown(self):
        url = '/v5/coach/workouts'
        params = {
            'type': 'cooldown'
        }
        return self.request('GET', url, params=params)

    def coach_workouts_warmup(self):
        url = '/v5/coach/workouts'
        params = {
            'type': 'warmup'
        }
        return self.request('GET', url, params=params)

    def best_trainings(self, user_id):
        url = f'/v3/coach/users/{user_id}/trainings/best'
        return self.request('GET', url)

    def training_coach(self, user_id):
        url = f'/payment/v1/claims/training-coach/{user_id}'
        return self.request('GET', url)

    def calendar(self):
        url = '/v7/calendar'
        return self.request('GET', url)

    def calendar_days(self, day):
        """
        .. note::
           date format: 2021-08-17
        """
        url = f'/v7/calendar/days/{day}'
        params = {
            'distance_unit_system': 'metric',
            'skill_paths_enabled': 'true',
            'weight_unit_system': 'metric'
        }
        return self.request('GET', url, params=params)

    def coach_session(self, session_id):
        url = f'/v6/coach/sessions/{session_id}'
        return self.request('GET', url)

    def coach_session_summary(self, session_id):
        url = f'/v6/coach/sessions/{session_id}/summary'
        params = {
            'distance_unit_system': 'metric',
            'skill_paths_enabled': 'true',
            'weight_unit_system': 'metric'
        }
        return self.request('GET', url, params=params)

    def planned_activities(self, activity_id):
        url = f'/v6/planned_activities/{activity_id}'
        return self.request('GET', url)

    def performed_activities(self, activity_id):
        url = f'/v6/performed_activities/{activity_id}'
        return self.request('GET', url)

    def social_feed(self):
        url = '/social/v1/feed'
        return self.request('GET', url)

    def user_activities(self, user_id):
        url = f'/social/v1/users/{user_id}/activities'
        return self.request('GET', url)

    def logout(self):
        url = '/user/v1/auth/logout'
        params = {
            'refresh_token': self._session.auth.refresh_token.token,
            'user_id': self._session.auth.refresh_token.user_id
        }
        return self.request('DELETE', url, params=params)


class FreeleticsClient(BaseClient):

    _SESSION = httpx.Client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self) -> None:
        self._session.close()

    def request(self, method, url, **kwargs):
        r = self._session.request(method, url, **kwargs)
        try:
            r.raise_for_status()
            r_json = r.json()
            print(json.dumps(r_json, indent=4))
            return r_json
        except json.JSONDecodeError:
            return r.text
        except:
            print(r.headers)
            print(r.request.headers)
            r.request.read()
            print(r.request._content)
            raise


class AsyncFreeleticsClient(BaseClient):

    _SESSION = httpx.AsyncClient

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def close(self) -> None:
        await self._session.aclose()

    async def request(self, method, url, **kwargs):
        r = await self._session.request(method, url, **kwargs)
        try:
            r.raise_for_status()
            r_json = r.json()
            print(json.dumps(r_json, indent=4))
            return r_json
        except json.JSONDecodeError:
            return r.text
        except:
            print(r.headers)
            print(r.request.headers)
            raise
