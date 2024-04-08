SHELL = /bin/bash
HOST_USER = $(shell whoami)
U_ID = $(shell id -u)
G_ID = $(shell id -g)
PROJECT_NAME = fotovoltaica-madrid
DEPS_GROUPS ?=
POETRY_DEPS = $(if $(DEPS_GROUPS),--with $(DEPS_GROUPS),)

.PHONY: default

default: help

##@
##@ Available commands
##@

dev/build: ##@ Build dev image
	## For the dev image, we need to install the test dependencies
	$(eval POETRY_DEPS := --with test)
	docker build \
		--build-arg U_ID=$(U_ID) \
		--build-arg G_ID=$(G_ID) \
		--build-arg USER=$(HOST_USER) \
		--build-arg PROJECT_NAME=$(PROJECT_NAME) \
		--build-arg DEPENDENCIES='$(POETRY_DEPS)' \
		-t $(PROJECT_NAME):dev . \
		-f devops/dev/Dockerfile

dev/run: dev/build ##@ Run interactive docker session with dev image and source code mounted
	docker run --rm -it \
		--gpus all \
		--user $(shell chmod 755 ./bin/get_docker_run_user.sh && ./bin/get_docker_run_user.sh) \
		-e HOME=/home/$(HOST_USER) \
		--network host \
		-v $(shell pwd):/home/$(HOST_USER)/$(shell basename $(shell pwd)) \
		--name $(PROJECT_NAME)-dev-container \
		$(PROJECT_NAME):dev bash

whl/build: poetry_runtime/build ##@ Build custom wheel of the project
	docker run --rm \
		--user $(shell chmod 755 ./bin/get_docker_run_user.sh && ./bin/get_docker_run_user.sh) \
		-v /home/$(USER)/.cache/pypoetry:/home/$(USER)/.cache/pypoetry \
		-v $(shell pwd):/home/$(USER)/$(shell basename $(shell pwd)) \
		--name $(PROJECT_NAME)-whl-builder-container \
		poetry-common bash -c "cd ${PROJECT_NAME} && poetry build ${POETRY_DEPS} --format wheel"

##@
##@ Poetry commands
##@

poetry_runtime/build: ##@ Build the docker image for running poetry
	docker build \
		--build-arg U_ID=$(U_ID) --build-arg G_ID=$(G_ID) --build-arg USER=$(HOST_USER) \
		-t poetry-common . \
		-f devops/common/poetry.Dockerfile

poetry_runtime/run: poetry_runtime/build ##@ Run interactive docker session with poetry image and source code mounted
	docker run --rm -it \
		--gpus all \
		--user $(shell chmod 755 ./bin/get_docker_run_user.sh && ./bin/get_docker_run_user.sh) \
		-e HOME=/home/$(HOST_USER) \
		-v /home/$(HOST_USER)/.cache/pypoetry:/home/$(HOST_USER)/.cache/pypoetry \
		-v $(shell pwd):/home/$(HOST_USER)/$(shell basename $(shell pwd)) \
		--name $(PROJECT_NAME)-poetry-container \
		poetry-common bash -c "cd ${PROJECT_NAME} && bash"

##@
##@ Misc commands
##@

# Adapted from: https://gist.github.com/prwhite/8168133?permalink_comment_id=4718682#gistcomment-4718682
help: ##@ (Default) Print listing of key targets with their descriptions
	@printf "\nUsage: make <command>\n"
	$(eval FORMAT_HELP_SPACES=$(shell grep -h "##@" Makefile | sed -e 's/:.*//' | grep -v "##@" | awk '{ print length }' | sort -n | tail -1))
	@grep -F -h "##@" $(MAKEFILE_LIST) | grep -F -v grep -F | sed -e 's/\\$$//' | sed -e 's/:.*##@/ ##@/' | awk -v spacing="$(FORMAT_HELP_SPACES)" 'BEGIN {FS = ":*[[:space:]]*##@[[:space:]]*"}; \
	{ \
		if($$2 == "") \
			pass; \
		else if($$0 ~ /^#/) \
			printf "\n%s\n", $$2; \
		else if($$1 == "") \
			printf "     %-*s%s\n", "", spacing + 4, $$2; \
		else \
			printf "    \033[34m%-*s\033[0m %s\n", spacing + 4, $$1, $$2; \
	}'
