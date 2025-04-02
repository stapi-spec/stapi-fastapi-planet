# STAT FastAPI - Planet

This is an example implementation for `https://github.com/stat-utils/stat-fastapi` proxying to the Planet Tasking API.


Start the server locally

```sh
uvicorn planet.application:app --app-dir ./src/planet --reload
```

GET all products
```sh
curl http://127.0.0.1:8000/products
```

POST to opportunities
```sh
export BACKEND_TOKEN=...
curl -d '{"geometry": {"type": "Point", "coordinates": [13.4, 52.5]}, "product_id": "PL-123456:Assured Tasking", "datetime": "2024-05-01T00:00:00Z/2024-05-12T00:00:00Z"}' -H "Content-Type: application/json; Authorization: $BACKEND_TOKEN" -X POST http://127.0.0.1:8000/opportunities
```
