# Backend GOlang

# User API

## ===> Registration

Request:
```bash
$ curl -i http://localhost:8080/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"login":"user123","password":"password123","full_name":"Some Name","phone":"8(999)111-22-33","email":"u@ex.com"}'
```

<details>

<summary><strong>Response</strong></summary>

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Vary: Origin
Date: Thu, 22 Jan 2026 18:30:13 GMT
Content-Length: 159

{
    "email":"u@ex.com",
    "full_name":"Some Name",
    "id":"7c5c646d-1816-4476-b5ee-a13ecfc48f51",
    "login":"user123",
    "phone":"8(999)111-22-33",
    "role":"user"
}
```

</details>

## ===> Authorisation

### JSON-response

Request:
```bash
$ curl -s http://localhost:8080/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"login":"user123","password":"password123"}'
```

<details>

<summary><strong>Response</strong></summary>

```json
{
    "token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiN2M1YzY0NmQtMTgxNi00NDc2LWI1ZWUtYTEzZWNmYzQ4ZjUxIiwibG9naW4iOiJ1c2VyMTIzIiwicm9sZSI6InVzZXIiLCJleHAiOjE3NjkxOTMyMTMsImlhdCI6MTc2OTEwNjgxM30.npwOQBsxlGgspLO_QWLoigX7PR5qIcgnSQYX2NgFhEU",
    "user":{
        "full_name":"Some Name",
        "id":"7c5c646d-1816-4476-b5ee-a13ecfc48f51",
        "login":"user123",
        "role":"user"
    }
}
```

</details>

### Token-response

Request:
```bash
$ TOKEN=$(curl -s http://localhost:8080/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"login":"user123","password":"password123"}' | jq -r .token)
echo "$TOKEN"
```

<details>

<summary><strong>Response</strong></summary>

```bash
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiN2M1YzY0NmQtMTgxNi00NDc2LWI1ZWUtYTEzZWNmYzQ4ZjUxIiwibG9naW4iOiJ1c2VyMTIzIiwicm9sZSI6InVzZXIiLCJleHAiOjE3NjkxOTM1NzcsImlhdCI6MTc2OTEwNzE3N30.XYZlvYEhmDqgpObsQLDY65hB6gw1pcj-UPlS37fHaV0
```

</details>

### EXAMPLE error response

Request:
```
$ curl -i http://localhost:8080/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"login":"user123","password":"wrongpass"}'
```

<details>

<summary><strong>Response</strong></summary>

```http
HTTP/1.1 401 Unauthorized
Content-Type: text/plain; charset=utf-8
Vary: Origin
X-Content-Type-Options: nosniff
Date: Thu, 22 Jan 2026 18:34:10 GMT
Content-Length: 26

invalid login or password
```

</details>

## ===> Check /me with Token

Request:
```bash
$ curl -i http://localhost:8080/api/me -H "Authorization: Bearer $TOKEN"
```

<details>

<summary><strong>Response</strong></summary>

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Vary: Origin
Date: Thu, 22 Jan 2026 18:41:31 GMT
Content-Length: 159

{
    "email":"u@ex.com",
    "full_name":"Some Name",
    "id":"7c5c646d-1816-4476-b5ee-a13ecfc48f51",
    "login":"user123",
    "phone":"8(999)111-22-33",
    "role":"user"
}
```

</details>

## ===> Create Item (request/content/etc.)

Request:
```bash
$ curl -i http://localhost:8080/api/requests \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"type":"service_visit","payload":{"car_brand":"Toyota","car_model":"Camry","date":"2026-01-25","problem":"Стук"}}'
```

<details>

<summary><strong>Response</strong></summary>

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Vary: Origin
Date: Thu, 22 Jan 2026 18:42:10 GMT
Content-Length: 317

{
    "id":"07498d85-bc19-47cf-a5e7-ec62bd12328f",
    "user_id":"7c5c646d-1816-4476-b5ee-a13ecfc48f51",
    "type":"service_visit",
    "payload":{
        "date":"2026-01-25",
        "problem":"Стук",
        "car_brand":"Toyota",
        "car_model":"Camry"
    },
    "status":"new",
    "created_at":"2026-01-22 18:42:10.621198+00",
    "updated_at":"2026-01-22 18:42:10.621198+00"
}
```

</details>

## ===> List Items (request/content/etc.)

Request:
```bash
$ curl -s http://localhost:8080/api/requests -H "Authorization: Bearer $TOKEN" | jq
```

<details>

<summary><strong>Response</strong></summary>

```json
{
    "items": [
        {
            "id": "07498d85-bc19-47cf-a5e7-ec62bd12328f",
            "user_id": "7c5c646d-1816-4476-b5ee-a13ecfc48f51",
            "type": "service_visit",
            "payload": {
                "date": "2026-01-25",
                "problem": "Стук",
                "car_brand": "Toyota",
                "car_model": "Camry"
            },
            "status": "new",
            "created_at": "2026-01-22 18:42:10.621198+00",
            "updated_at": "2026-01-22 18:42:10.621198+00"
        }
    ]
}
```

</details>

## ===> Post Feedback

Request for Item #0 ID:
```bash
$ ITEM_ID=$(curl -s http://localhost:8080/api/requests -H "Authorization: Bearer $TOKEN" | jq -r .items[0].id)
echo $ITEM_ID
```

<details>

<summary><strong>Response</strong></summary>

```bash
07498d85-bc19-47cf-a5e7-ec62bd12328f
```

</details>

Request Feedback:
```bash
$ curl -i http://localhost:8080/api/requests/$ITEM_ID/feedback \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"rating":5,"comment":"OK!"}'
```

<details>

<summary><strong>Response</strong></summary>

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Vary: Origin
Date: Fri, 23 Jan 2026 10:33:06 GMT
Content-Length: 219

{
    "id":"76b97123-5621-41fd-a14a-85f73f29f806",
    "request_id":"07498d85-bc19-47cf-a5e7-ec62bd12328f",
    "user_id":"7c5c646d-1816-4476-b5ee-a13ecfc48f51",
    "rating":5,
    "comment":"OK!",
    "created_at":"2026-01-23 10:33:06.264058+00"
}
```

</details>

# Admin API

## ===> Authorisation

Password is set in `ADMIN_SEED_PASSWORD`.

Request:
```bash
$ ADM_TOKEN=$(curl -s http://localhost:8080/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"login":"Admin","password":"Admin12345!"}' | jq -r .token)

echo "$ADM_TOKEN"
```

<details>

<summary><strong>Response</strong></summary>

```bash
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiY2Q4NmZkZTUtMGJiNi00ZDFmLTkwZmEtODFlOTdiNGFjYzk1IiwibG9naW4iOiJBZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2OTI1MTc3OSwiaWF0IjoxNzY5MTY1Mzc5fQ.GgOHrWZUOC4FyNkSPkeM2MYSM-fQyIaoBpEMpyXOLrI
```

</details>

## ===> List Items (request/content/etc.)

Request:
```bash
$ curl -s http://localhost:8080/api/admin/requests -H "Authorization: Bearer $ADM_TOKEN" | jq
```

<details>

<summary><strong>Response</strong></summary>

```json
{
    "items": [
        {
            "id": "07498d85-bc19-47cf-a5e7-ec62bd12328f",
            "user_id": "7c5c646d-1816-4476-b5ee-a13ecfc48f51",
            "user_login": "user123",
            "type": "service_visit",
            "payload": {
                "date": "2026-01-25",
                "problem": "Стук",
                "car_brand": "Toyota",
                "car_model": "Camry"
            },
            "status": "new",
            "created_at": "2026-01-22 18:42:10.621198+00",
            "updated_at": "2026-01-22 18:42:10.621198+00"
        }
    ]
}
```

</details>

## ===> Change Item status (request/content/etc.)

Request for Item #0 ID:
```bash
$ ITEM_ID=$(curl -s http://localhost:8080/api/admin/requests -H "Authorization: Bearer $ADM_TOKEN" | jq -r .items[0].id)
echo $ITEM_ID
```

<details>

<summary><strong>Response</strong></summary>

```bash
07498d85-bc19-47cf-a5e7-ec62bd12328f
```

</details>

Request change status:
```bash
$ curl -i -X PATCH http://localhost:8080/api/admin/requests/$ITEM_ID/status \
    -H "Authorization: Bearer $ADM_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status":"in_progress","admin_comment":"In progress"}'
```

<details>

<summary><strong>Response</strong></summary>

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Vary: Origin
Date: Fri, 23 Jan 2026 11:01:59 GMT
Content-Length: 12

{"ok":true}
```

</details>
