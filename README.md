# aio_bot

```bash
openssl genrsa -out src/backend/ssl/cert.key 2048
openssl req -new -x509 -key src/backend/ssl/cert.key -out src/backend/ssl/cert.crt -days 365
```

