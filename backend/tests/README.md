# Backend tests

Requires a disposable Postgres instance on port 55432:

```sh
docker compose -f backend/tests/docker-compose.test.yml up -d
```

Then, from the repo root:

```sh
uv run pytest backend/tests
```

Tear the database back down with:

```sh
docker compose -f backend/tests/docker-compose.test.yml down
```
