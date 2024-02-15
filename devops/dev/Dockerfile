FROM mambaorg/micromamba:jammy

USER root

ARG USER_NAME=fotovoltaica
ARG USER_UID=1000
ARG USER_GID=1000

ARG USER_NAME=$USER_NAME
ARG USER_UID=$USER_UID
ARG USER_GID=$USER_GID

RUN if grep -q '^ID=alpine$' /etc/os-release; then \
      # alpine does not have usermod/groupmod
      apk add --no-cache --virtual temp-packages shadow; \
    fi && \
    usermod "--login=${USER_NAME}" "--home=/home/${USER_NAME}" \
      --move-home "-u ${USER_UID}" "${MAMBA_USER}" && \
    if getent group "${USER_GID}" >/dev/null; then \
      echo "Group exists" && \
      usermod -aG "${USER_GID}" "${USER_NAME}"; \
    else \
      echo "Group does not exist" && \
      groupmod "--new-name=${USER_NAME}" \
        "-g ${USER_GID}" "${MAMBA_USER}"; \
    fi && \
    if grep -q '^ID=alpine$' /etc/os-release; then \
      # remove the packages that were only needed for usermod/groupmod
      apk del temp-packages; \
    fi && \
    # Update the expected value of MAMBA_USER for the
    # _entrypoint.sh consistency check.
    echo "${USER_NAME}" > "/etc/arg_mamba_user" && \
    :

ENV MAMBA_USER=$USER_NAME
USER $MAMBA_USER

# This part should be commented the first time if no environment.yml is provided
# Thus, installing all the required packages with `micromamba install -c conda-forge -c defaults ... <package>`
# this can included pip packages as well.
# Then, generate the environment.yml with `micromamba env export -f environment.yml` and save the file.
# If the pip packages are not present in the environment.yml, append then manually at the end of the file including
# ```
# - pip:
#   - <pip_package_1>
#   - <pip_package_2>
#```
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

WORKDIR /app