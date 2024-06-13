# =============================================== General Dockerfile ARGs ==============================================
ARG DEBIAN_CODENAME="bullseye"
ARG PYTHON_VERSION=3.11
ARG PIPX_VERSION=1.6.0
ARG POETRY_VERSION=1.8.3
# Note: runtime matches the debian bullseye version 11 under ITG cluster gpu nodes
ARG RUNTIME_BASE="python:$PYTHON_VERSION-slim-$DEBIAN_CODENAME"
# These input ARG are managed through Makefile
ARG USER
ARG U_ID
ARG G_ID
# Setting home environment
ARG HOME="/home/$USER"

FROM $RUNTIME_BASE AS runtime
ARG PIPX_VERSION
ARG POETRY_VERSION
ARG USER
ARG U_ID
ARG G_ID
ARG HOME

WORKDIR $HOME
# Install pipx for poetry: https://python-poetry.org/docs/
RUN pip install --no-cache-dir pipx=="$PIPX_VERSION" && \
    pipx install poetry=="$POETRY_VERSION"

# Set initial envs for poetry, note the venv is created in the project dir under .venv
ENV POETRY_INSTALLER_MAX_WORKERS=10 \
    PATH=$HOME/.local/bin:$PATH

# ============================ Setting non-root nlpuser and group + final settings =====================================
COPY --chmod=755 ./bin/set_uid_gid.sh ./
# check if current user/group ids already exist, otherwise create it and assign the user name (whoami) and he group id
RUN /bin/bash set_uid_gid.sh "$U_ID" "$G_ID" "$USER" && rm -rf ./set_uid_gid.sh
RUN chown -R "$U_ID":"$G_ID" "$HOME"
RUN chmod 755 "$HOME"

USER $USER
