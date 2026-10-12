# API Reference

Base URL: `https://api.meridian.example/v1`

Authenticate with a bearer token:

```
Authorization: Bearer <token>
```

Generate tokens under Settings > API Keys. Tokens inherit the permissions of
the user who created them.

## Create a deploy

`POST /v1/deploys`

Body:

```json
{"app": "my-app", "region": "us-west"}
```

Returns `{"id": "dpl_123", "status": "building"}`.

## Get deploy status

`GET /v1/deploys/{id}` returns `{"status": "ready"}` when the deploy is live.
