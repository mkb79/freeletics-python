"""
Inspired from http://topu.ch/it/reverse-engineering-des-freeletics-apis/
"""


import json
import logging

import httpx


logger = logging.getLogger(__name__)

BASE_URL = 'https://api.freeletics.com/'


class FreeleticsAuth(httpx.Auth):
    def __init__(self, id_token, refresh_token, user_id):
        self.id_token = id_token
        self.refresh_token = refresh_token
        self.user_id = user_id

    def auth_flow(self, request):
        # Send the request, with a custom `X-Authentication` header.
        request.headers['Authorization'] = f'Bearer {self.id_token}'
        response = yield request

        if response.status_code == 401 or response.status_code == 419:
            # If the server issues a 401 response, then issue a request to
            # refresh tokens, and resend the request.
            refresh_response = self.build_refresh_request()
            self.update_token(refresh_response)

            request.headers['Authorization'] = f'Bearer {self.id_token}'
            yield request

    def build_refresh_request(self):
        # Return an `httpx.Request` for refreshing tokens.

        logger.info('Requesting new id_token')
        data = {
          "user_id" : self.user_id,
          "refresh_token" : self.refresh_token
        }
        with httpx.Client(base_url=BASE_URL) as client:
            url = '/user/v1/auth/refresh'
            return client.post(url, json=data)

    def update_token(self, response):
        # Update the `.access_token` and `.refresh_token` tokens
        # based on a refresh response.
        data = response.json()
        self.id_token = data['auth']['id_token']
        logger.info(f'Got new id_token {self.id_token}')
        

class FreeleticsClient:
    def __init__(self, id_token, refresh_token, user_id):
        auth = FreeleticsAuth(
            id_token=id_token,
            refresh_token=refresh_token,
            user_id=user_id)
        headers = {
            'Accept': 'application/json'
        }
        self._session = httpx.Client(auth=auth, headers=headers, base_url=BASE_URL)

    def request(self, method, url, **kwargs):
        r = self._session.request(method, url, **kwargs)
        try:
            r.raise_for_status()
            return r.json()
        except json.JSONDecodeError:
            return r.text
        except:
            print(r.headers)
            raise

    def login(self, username, password):
        """
        Doesnt work at this moment. Server raises a HTTP Status Code 426.
        Have to find out how X-Authorization header is created.
        """
        print('This method doesnt work at this time')
        url = '/user/v2/password/authentication'
        headers = {
            'X-Authorization': 'None',
            'X-Authorization-Timestamp': 'None'
        }
        data = {
            "authentication": {
                "email": username,
                "password": password
            }
        }
        return self.request("POST", url, json=data, headers=headers, auth=None)

    def login_old(self, username, password):
        """
        Doesnt work at this moment. Server raises a HTTP Status Code 426.
        """
        print('This method doesnt work at this time!')
        url = '/user/v1/auth/password/login'
        data = {
            'login': {
                "email": username,
                "password": password
            }
        }
        return self.request("POST", url, json=data, auth=None)

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
            'refresh_token': self._session.auth.refresh_token,
            'user_id': self._session.auth.user_id
        }
        return self.request('DELETE', url, params=params)

