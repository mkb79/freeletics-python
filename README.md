# Freeletics API Client (unofficial)


**This Client communicate with the non-publicly [Freeletics](https://www.freeletics.com) API.**

**This Client is still in progress. Help is welcome!**

## Current progress

Working on data models for API response and ETag/If-None-Match header to reduce traffic.

## Basic Usage

```python
from freeletics.client import FreeleticsClient 

with FreeleticsClient() as client:
    client.login(USERNAME, PASSWORD)
    payment, header = client.payment()
    profile, header = client.profile()
    client.logout()
```

Do not forget to logout. Otherwise the refresh token will not be deleted on the server. I does not know what will happend, if you have multiple unused refresh tokens.