# Freeletics API Client (unofficial)

**This Client communicate with the non-publicly [Freeletics](https://www.freeletics.com) API.**

**This Client is still in progress. Help is welcome!**

## Current progress

Working on data models for API response and ETag/If-None-Match header to reduce traffic.

## Requirements

freeletics needs at least _Python 3.8_.

It depends on the following packages:

- httpx >= 0.24.0
- pyjwt

## Installation

This package is not on PyPi at this moment. To install freeletics you have to clone it from this repo.

```shell

git clone https://github.com/mkb79/freeletics-python.git
cd freeletics-python
pip install .

```

## Basic Usage

```python
from freeletics import FreeleticsClient

with FreeleticsClient() as client:
    client.login(USERNAME, PASSWORD)
    payment = client.get_payment_claims()
    profile = client.get_user_profile()
    client.logout()
```

**Do not forget to log out. Otherwise, the refresh token will not be deleted on the server. I do not know what will happen, if you have multiple unused refresh tokens.**

## Advanced Usage

If you do not want to log in everytime, you can reuse the session this way:

```python
from freeletics import Credentials, FreeleticsClient

with FreeleticsClient() as client:
    client.login(USERNAME, PASSWORD)
    cred = client.get_credentials()
    cred.to_file(FILENAME)

cred = Credentials.from_file(FILENAME).as_dict()
with FreeleticsClient.from_credentials(**cred) as client:
    ...
```

Important note:
Please be careful when the client refresh the `id_token`. Do not use the old `id_token` again. Otherwise, the Freeletics API server will quit this with an HTTP Error 404 (when the old `id_token` is expired) and your `refresh_token` will be invalid.

@Freeletics engineers:
It would be very helpful if you open your API. My goal is only to get my personal training stats from the API. If there is a way please contact me.
