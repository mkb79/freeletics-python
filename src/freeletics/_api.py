from typing import Optional, Union

from httpx._models import URL, Cookies, Headers, QueryParams, Request
from httpx._types import (
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    URLTypes
)


BASE_URL: str = 'https://api.freeletics.com'
DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'Accept-Encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8'
}


class ApiRequestBuilder:
    def __init__(self, session) -> None:
        self._session = session
        self._base_url = URL(BASE_URL)
        self._cookies = Cookies(None)
        self._headers = Headers(DEFAULT_HEADERS)
        self._params = QueryParams(None)

    def _merge_url(self, url: URLTypes) -> URL:
        """
        Merge a URL argument together with any 'base_url' on the client,
        to create the URL used for the outgoing request.
        """
        merge_url = URL(url)
        if merge_url.is_relative_url:
            # We always ensure the base_url paths include the trailing '/',
            # and always strip any leading '/' from the merge URL.
            merge_url = merge_url.copy_with(path=merge_url.path.lstrip("/"))
            return self._base_url.join(merge_url)
        return merge_url

    def _merge_cookies(
        self, cookies: CookieTypes = None
    ) -> Optional[CookieTypes]:
        """
        Merge a cookies argument together with any cookies on the client,
        to create the cookies used for the outgoing request.
        """
        if cookies or self._cookies:
            merged_cookies = Cookies(self._cookies)
            merged_cookies.update(cookies)
            return merged_cookies
        return cookies

    def _merge_headers(
        self, headers: HeaderTypes = None
    ) -> Optional[HeaderTypes]:
        """
        Merge a headers argument together with any headers on the client,
        to create the headers used for the outgoing request.
        """
        merged_headers = Headers(self._headers)
        merged_headers.update(headers)
        return merged_headers

    def _merge_queryparams(
        self, params: QueryParamTypes = None
    ) -> Optional[QueryParamTypes]:
        """
        Merge a queryparams argument together with any queryparams on the client,
        to create the queryparams used for the outgoing request.
        """
        if params or self._params:
            merged_queryparams = QueryParams(self._params)
            merged_queryparams = merged_queryparams.merge(params)
            return merged_queryparams
        return params

    def _build_request(self,
                       method: str,
                       url: URLTypes,
                       *,
                       params: QueryParamTypes = None,
                       headers: HeaderTypes = None,
                       cookies: CookieTypes = None,
                       **kwargs) -> Request:
        url = self._merge_url(url)
        headers = self._merge_headers(headers)
        cookies = self._merge_cookies(cookies)
        params = self._merge_queryparams(params)
        return self._session.build_request(method,
                                           url,
                                           headers=headers,
                                           cookies=cookies,
                                           params=params,
                                           **kwargs)

    def request(self, method: str, url: str, **kwargs) -> Request:
        return self._build_request(method, url, **kwargs)

    def get_calendar(self, payment_token: str) -> Request:
        url = '/v7/calendar'
        headers = {'Payment-Token': payment_token}
        return self._build_request('GET', url, headers=headers)

    def get_calendar_by_date(self,
                             date: str,
                             payment_token: str,
                             distance_unit_system: str = 'metric',
                             weight_unit_system: str = 'metric',
                             skill_paths_enabled: str = 'true'
                             ) -> Request:
        """
        .. note::
           date format: 2021-08-17
        """
        url = '/v7/calendar/days/' + date
        headers = {'Payment-Token': payment_token}
        params = {
            'distance_unit_system': distance_unit_system,
            'skill_paths_enabled': skill_paths_enabled,
            'weight_unit_system': weight_unit_system
        }
        return self._build_request('GET', url, headers=headers,
                                           params=params)

    def get_coach_exercises(self) -> Request:
        url = '/v5/coach/exercises'
        return self._build_request('GET', url)

    def get_coach_settings(self) -> Request:
        url = '/v5/coach/settings'
        return self._build_request('GET', url)

    def get_coach_workouts(self, type_: str) -> Request:
        """
        known types: god, exercise_workout, run, cooldown, warmup
        """
        url = '/v5/coach/workouts'
        params = {'type': type_}
        return self._build_request('GET', url, params=params)

    def get_messsging_profile(self) -> Request:
        url = '/messaging/v1/profile'
        return self._build_request('GET', url)

    def get_payment_claims(self, supported_brand_types: Optional[str] = None
                           ) -> Request:
        url = '/payment/v3/claims'

        if supported_brand_types is None:
            supported_brand_types = 'bodyweight-coach,nutrition-coach,' \
                                    'gym-coach,running-coach,training-coach,' \
                                    'training-nutrition-coach,mind-coach,' \
                                    'mind-training-nutrition-coach'

        params = {'supported_brand_types': supported_brand_types}
        return self._build_request('GET', url, params=params)

    def get_payment_training_coach_by_userid(self, user_id: Union[str, int]
                                             ) -> Request:
        url = '/payment/v1/claims/training-coach/' + str(user_id)
        return self._build_request('GET', url)

    def get_performed_activities_by_id(self, activity_id: Union[str, int]
                                       ) -> Request:
        url = '/v6/performed_activities/' + str(activity_id)
        return self._build_request('GET', url)

    def get_planned_activities_by_id(self, activity_id: Union[str, int]
                                     ) -> Request:
        url = '/v6/planned_activities/' + str(activity_id)
        return self._build_request('GET', url)

    def get_social_feeds(self) -> Request:
        url = '/social/v1/feed'
        return self._build_request('GET', url)

    def get_status_bodyweight_app(self) -> Request:
        url = '/user/v1/status/bodyweight/'
        return self._build_request('GET', url)

    def get_user_activities_by_id(self, user_id: Union[str, int],
                                  page: Optional[Union[str, int]] = None
                                  ) -> Request:
        url = '/social/v1/users/' + str(user_id) + '/activities'
        params = {}
        if page is not None:
            params['page'] = str(page)
        return self._build_request('GET', url, params=params)

    def get_user_profile(self) -> Request:
        url = '/v4/profile'
        return self._build_request('GET', url)

    def get_user_status_general(self) -> Request:
        url = '/user/v1/status/general/'
        return self._build_request('GET', url)

    def login_user(self, username: str, password: str) -> Request:
        """
        Does not work at this moment. Server raises a HTTP Status Code 426.
        Login request have to be signed using a `X-Authorization` and 
        `X-Authorization-Timestamp` header. 
        Have to find out how X-Authorization token is created.
        Update: Have found out that the request body is part of the signing
                process. Using signing headers from a fresh login with the
                iOS Freeletics App let me login with my Client, if the request
                body is formed (remove whitespaces) like the iOS App does.
        Update 2: Thanks to the Tipp from here 
                  (https://freeletics.engineering/2019/10/30/shared_login.html)
                  I have a working workarount to login. Simply using User-Agent
                  from Nutrion App.
        """
        url = '/user/v2/password/authentication'

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'nutrition-ios-1083 (iPhone; iOS 14.7.1; Nutrition '
                          '1.30.1; com.freeletics.nutrition; en_GB; BST; '
                          'release)'
        }

        data = {"authentication": {"email": username, "password": password}}
        # data = json.dumps(data, separators=(',', ':'))
        return self._build_request("POST", url, json=data,
                                           headers=headers)

    def logout_user(self, refresh_token: str,
                    user_id: Union[str, int]) -> Request:
        url = '/user/v1/auth/logout'
        params = {
            'refresh_token': refresh_token,
            'user_id': str(user_id)
        }
        return self._build_request('DELETE', url, params=params)

    def search_user_by_phrase(self, phrase: Optional[str] = None,
                              page: Optional[Union[str, int]] = None
                              ) -> Request:
        url = '/v2/users/search'

        data = {}
        if phrase is not None:
            data['phrase'] = phrase
        if page is not None:
            data['page'] = str(page)

        return self._build_request('POST', url, json=data)

    def update_id_token(self, refresh_token: str, user_id: Union[str, int]
                        ) -> Request:
        url = '/user/v1/auth/refresh'
        data = {"user_id": str(user_id), "refresh_token": refresh_token}
        return self._build_request('POST', url, json=data)
