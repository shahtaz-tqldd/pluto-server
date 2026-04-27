# Pluto API Documentation

This repository already exposes live schema and browser docs:

- `GET /api/schema/` - OpenAPI schema
- `GET /api/docs/` - Swagger UI
- `GET /api/redoc/` - ReDoc

This document is a code-backed reference for the current API surface in the repo, plus the matching Postman assets in `docs/postman/`.

## Base URLs

- Local dev app: `http://localhost:9065`
- API root: `http://localhost:9065/api/v1`
- Admin API root: `http://localhost:9065/api/v1/admin`

## Authentication

Most protected endpoints use:

`Authorization: Bearer <access_token>`

Tokens are returned by:

- `POST /api/v1/auth/login/`
- `POST /api/v1/admin/auth/admin-register/`
- `POST /api/v1/auth/refresh/`

## Common Response Shape

Successful responses use this envelope:

```json
{
  "status": 200,
  "success": true,
  "message": "Success",
  "data": {},
  "meta": {}
}
```

Error responses use this envelope:

```json
{
  "status": 400,
  "success": false,
  "message": "An error occured!",
  "errors": {
    "field": ["message"]
  }
}
```

## Postman Assets

- Collection: `docs/postman/Pluto API.postman_collection.json`
- Environment: `docs/postman/Pluto Local.postman_environment.json`

Import both files into Postman, then set these variables as you get real IDs from your database:

- `baseUrl`
- `accessToken`
- `refreshToken`
- `petId`
- `conversationId`
- `adopterId`
- `rescuerId`
- `adminId`
- `requestId`
- `inviteToken`

## Endpoint Reference

### System Docs

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/api/schema/` | No | OpenAPI schema |
| GET | `/api/docs/` | No | Swagger UI |
| GET | `/api/redoc/` | No | ReDoc |

### Client Auth

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register/` | No | Register adopter or rescuer user |
| POST | `/api/v1/auth/login/` | No | Login with email and password |
| POST | `/api/v1/auth/refresh/` | No | Exchange refresh token for access token |
| GET | `/api/v1/auth/user-details/` | Bearer | Current user profile |
| PATCH | `/api/v1/auth/user-details/update/` | Bearer | Update current user basics |
| PATCH | `/api/v1/auth/change-password/` | Bearer | Change current password |

Request body highlights:

- `register`: optional `role` (`ADOPTER` by default, or `RESCUER`), `name`, `email` or `phone`, `password`, `confirm_password`
- `login`: `email`, `password`
- `refresh`: `refresh`
- `user-details/update`: multipart or form-data supported
- `change-password`: `current_password`, `new_password`, `confirm_password`

### Admin Auth

| Method | Path | Auth | Role |
| --- | --- | --- | --- |
| GET | `/api/v1/admin/auth/adopter/list/` | Bearer | Admin |
| GET | `/api/v1/admin/auth/admin-users/` | Bearer | Superadmin |
| PATCH | `/api/v1/admin/auth/admin-users/{admin_id}/` | Bearer | Superadmin |
| DELETE | `/api/v1/admin/auth/admin-users/{admin_id}/` | Bearer | Superadmin |
| POST | `/api/v1/admin/auth/send-invitation/` | Bearer | Admin |
| GET | `/api/v1/admin/auth/verify-invitation/?token=...` | No | Public |
| POST | `/api/v1/admin/auth/admin-register/` | No | Public invite completion |

Request body highlights:

- `send-invitation`
  - `email`
  - `job_title`
  - `permissions`: array of `{ "module": "...", "actions": ["VIEW", "CREATE"] }`
  - `expires_in_hours`
- `admin-users/{admin_id}` patch
  - `job_title`
  - `permissions`
- `admin-register`
  - `token`
  - `name`
  - `phone`
  - `password`
  - `confirm_password`

Known admin permission modules:

- `PET_LISTING_MANAGEMENT`
- `USER_MANAGEMENT`
- `ADOPTION_MANAGEMENT`

Known admin permission actions:

- `VIEW`
- `CREATE`
- `UPDATE`
- `DELETE`

### Adopters

| Method | Path | Auth | Role |
| --- | --- | --- | --- |
| GET | `/api/v1/adopters/me/` | Bearer | Adopter |
| PATCH | `/api/v1/adopters/me/` | Bearer | Adopter |
| GET | `/api/v1/adopters/adoption-requests/` | Bearer | Adopter |
| POST | `/api/v1/adopters/pets/{pet_id}/adoption-request/` | Bearer | Adopter |
| GET | `/api/v1/adopters/conversations/` | Bearer | Adopter |
| GET | `/api/v1/adopters/public/{adopter_id}/` | No | Public |
| GET | `/api/v1/adopters/public/{adopter_id}/reviews/` | No | Public |
| POST | `/api/v1/adopters/public/{adopter_id}/reviews/` | Bearer | Rescuer or Admin |

Request body highlights:

- `PATCH /adopters/me/`
  - multipart or form-data
  - supports `avatar_file`
  - profile fields: `home_type`, `pet_experience`, `preferred_pet_type`
- `POST /pets/{pet_id}/adoption-request/`
  - `intention`
  - `message`
- `POST /public/{adopter_id}/reviews/`
  - `rating` from 1 to 5
  - `message`

### Rescuers

| Method | Path | Auth | Role |
| --- | --- | --- | --- |
| GET | `/api/v1/rescuers/me/` | Bearer | Rescuer |
| PATCH | `/api/v1/rescuers/me/` | Bearer | Rescuer |
| GET | `/api/v1/rescuers/dashboard/` | Bearer | Rescuer |
| GET | `/api/v1/rescuers/public/{rescuer_id}/` | No | Public |
| GET | `/api/v1/rescuers/public/{rescuer_id}/reviews/` | No | Public |
| POST | `/api/v1/rescuers/public/{rescuer_id}/reviews/` | Bearer | Adopter or Admin |
| GET | `/api/v1/rescuers/adoption-requests/` | Bearer | Rescuer |
| POST | `/api/v1/rescuers/adoption-requests/{request_id}/accept/` | Bearer | Rescuer |
| POST | `/api/v1/rescuers/adoption-requests/{request_id}/reject/` | Bearer | Rescuer |
| GET | `/api/v1/rescuers/conversations/` | Bearer | Rescuer |
| POST | `/api/v1/rescuers/pets/{pet_id}/mark-adopted/` | Bearer | Rescuer |

Request body highlights:

- `PATCH /rescuers/me/`
  - multipart or form-data
  - supports `avatar_file`
  - profile fields: `organization_name`, `experience_years`
  - serializer also accepts `verification_status`, `successful_adoptions`, `response_rate`
- `POST /public/{rescuer_id}/reviews/`
  - `rating` from 1 to 5
  - `message`
- `POST /adoption-requests/{request_id}/{action}/`
  - no body required
  - `action` must be `accept` or `reject`

### Pets

| Method | Path | Auth | Role |
| --- | --- | --- | --- |
| GET | `/api/v1/pets/feed/` | No | Public |
| GET | `/api/v1/pets/` | No | Public |
| POST | `/api/v1/pets/` | Bearer | Rescuer |
| GET | `/api/v1/pets/{id}/` | No | Public |
| PATCH | `/api/v1/pets/{id}/` | Bearer | Pet owner or Admin |
| DELETE | `/api/v1/pets/{id}/` | Bearer | Pet owner or Admin |

Feed query params:

- `search`
- `species`
- `breed`
- `location`
- `available_only` default `true`
- `nearby` filters against authenticated user location
- `sort` one of `latest`, `oldest`, `most_interested`
- pagination params from custom paginator, typically `page` and `page_size`

Pet write body highlights:

- JSON or multipart depending on client
- fields:
  - `title`
  - `species`
  - `breed`
  - `gender`
  - `age_months`
  - `size`
  - `color`
  - `vaccinated`
  - `sterilized`
  - `medical_notes`
  - `temperament`
  - `story`
  - `current_location`
  - `rescue_location`
  - `status`
  - `images` as a file list
  - `remove_image_ids` as UUID list on update

Known pet enums:

- `species`: `DOG`, `CAT`, `BIRD`, `RABBIT`, `OTHER`
- `gender`: `MALE`, `FEMALE`, `UNKNOWN`
- `size`: `SMALL`, `MEDIUM`, `LARGE`, `EXTRA_LARGE`
- `status`: `DRAFT`, `AVAILABLE`, `PENDING`, `ADOPTED`, `ON_HOLD`, `ARCHIVED`

### Messages

| Method | Path | Auth | Role |
| --- | --- | --- | --- |
| GET | `/api/v1/messages/conversations/{conversation_id}/` | Bearer | Conversation participant |
| GET | `/api/v1/messages/conversations/{conversation_id}/messages/` | Bearer | Conversation participant |
| POST | `/api/v1/messages/conversations/{conversation_id}/messages/` | Bearer | Conversation participant |

Request body highlights:

- `POST /messages/.../messages/`
  - `body`

Conversation notes:

- Messages can only be sent while the conversation status is `ACTIVE`.
- A rescuer accepting an adoption request creates or reopens the conversation.

## Implementation Notes

The reference above was derived from the current route, view, serializer, and model code in:

- `app/urls.py`
- `auth/api/v1/**`
- `adopters/api/v1/**`
- `rescuers/api/v1/**`
- `pets/api/v1/**`
- `messages/api/v1/**`
