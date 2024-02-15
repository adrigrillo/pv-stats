DEV_IMAGE=fotovoltaica-madrid

dev/build:
	DOCKER_BUILDKIT=1 docker build \
			--build-arg USER_NAME=vision-dataset \
			--build-arg USER_UID=$(shell id -u) \
			--build-arg USER_GID=$(shell id -g) \
            -t ${DEV_IMAGE} \
            -f devops/dev/Dockerfile \
            .

dev/shell: dev/build
	docker run \
		-it \
		--rm \
		-v ${PWD}:/app \
		${DEV_IMAGE} \
		/bin/bash