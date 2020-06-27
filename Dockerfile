FROM python:3.7-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

# build the app and package into a venv
FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.0.2

RUN apk add \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
    --no-cache alpine-sdk libffi-dev musl-dev postgresql-dev libxml2-dev libxslt-dev geos-dev
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes | /venv/bin/pip install -r /dev/stdin

COPY . .
RUN poetry build && /venv/bin/pip install dist/*.whl

# copy the venv and the run scripts
FROM base as final

RUN apk add \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
    --no-cache libffi libpq geos libspatialite
RUN mv /usr/lib/mod_spatialite.so.7 /usr/lib/mod_spatialite.so
COPY --from=builder /venv /venv
COPY run.py entry.sh ./
CMD ["./entry.sh"]
