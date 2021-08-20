# Freeletics API Client (unofficial)


**This Client communicate with the non-publicly [Freeletics](https://www.freeletics.com) API.**

**This Client is still in progress. Help is welcome!**

**Important:**
For using this Client you are needing a `refresh token` and your `user_id` and/or a valid `id_token`.

## Current progress

Working currently on login part. The server raises a HTTP Status Code 426 on login. Reason is missing authenticaton header. Login request have to be signed using a `X-Authorization` and 
`X-Authorization-Timestamp` header. Have to find out how X-Authorization token is created.

Update: Have found out that the request body is part of the signing process. Using signing headers from a fresh login with the iOS Freeletics App let me login with my Client, if the request body is formed (remove whitespaces) like the iOS App does.

I would be happy if someone can help out!
