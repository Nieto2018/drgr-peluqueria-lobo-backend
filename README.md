# drgr-peluqueria-lobo-backend

Currently working on the project.

#

Old configuration for Heroku:

```text
# Procfile
web: gunicorn -w 1 -k uvicorn.workers.UvicornWorker backend.wsgi:application --log-file -
```
