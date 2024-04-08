ARG DEBIAN_CODENAME="bullseye"
ARG PYTHON_VERSION=3.11
ARG PIPX_VERSION=1.5.0
ARG POETRY_VERSION=1.8.2
ARG BUILD_BASE="python:$PYTHON_VERSION-slim-$DEBIAN_CODENAME"
ARG RUNTIME_BASE="python:$PYTHON_VERSION-slim-$DEBIAN_CODENAME"
# These input ARG are managed through makefile
ARG USER
ARG U_ID
ARG G_ID
# Setting home environment
ARG PROJECT_NAME
ARG HOME="/home/$USER"
ARG VENV_DIR="$HOME/.venv"

# Dependencies settings
ARG DEPENDENCIES

FROM $BUILD_BASE AS build
ARG PIPX_VERSION
ARG POETRY_VERSION
ARG HOME
ARG VENV_DIR
ARG DEPENDENCIES

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on

RUN pip install pipx=="$PIPX_VERSION" && \
    pipx install poetry=="$POETRY_VERSION" && \
    pipx inject poetry poetry-plugin-export && \
    python3 -m venv "$VENV_DIR"

ENV POETRY_NO_INTERACTION=1 \
    PATH=$HOME/.local/bin:${VENV_DIR}/bin:$PATH

WORKDIR $HOME
COPY pyproject.toml poetry.lock ./
RUN touch README.md && \
    poetry export --without-hashes ${DEPENDENCIES} -f requirements.txt -o requirements.txt && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

FROM $RUNTIME_BASE AS runtime
ARG PYTHON_VERSION
ARG USER
ARG U_ID
ARG G_ID
ARG PROJECT_NAME
ARG HOME
ARG VENV_DIR
ARG HF_TOKEN_FILE
ARG MINIO_CREDENTIALS_FILE

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=${VENV_DIR}/bin:${PATH} \
    PYTHONPATH=${HOME}/${PROJECT_NAME}:${PYTHONPATH}

# ============================ Setting non-root nlpuser and group + final settings =====================================
COPY --chmod=755 ./bin/set_uid_gid.sh ./
# check if current group id is already exists, otherwise create it with the user name at hand (whoami)
# Check if current user id already exists, otherwise create it and assign the user name (whoami) and he group id at hand
RUN /bin/bash set_uid_gid.sh "$U_ID" "$G_ID" "$USER" && rm -rf ./set_uid_gid.sh

USER $USER
WORKDIR $HOME

COPY --from=build --chown=$USER:$USER --chmod=755 $VENV_DIR $VENV_DIR
