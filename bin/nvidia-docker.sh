#!/bin/bash
distributions="amzn2 amzn2017.09 amzn2018.03  sles15.0  sles15.1 debian9 debian10 debian11 centos7 centos8 rhel7.4 rhel7.5 rhel7.6 rhel7.7 rhel7.8 rhel7.9 rhel8.0 rhel8.1 rhel8.2 rhel8.3 rhel8.4 rhel8.5 ubuntu16.04 ubuntu18.04 ubuntu19.04 ubuntu19.10 ubuntu20.04 ubuntu22.04"
if [ -z "$distribution" ]
then
	distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
fi

export GPU_ID=`nvidia-smi -a | grep UUID | awk '{print substr($4,0,12)}'`

if [[ $distributions =~ $distribution ]]; then
	echo "Installing nvidia-container-runtime for distribution '$distribution'"
else
	echo "Distribution '$distribution' not found in distribtutions:"
	echo "$distributions"
	echo
	echo "Export 'distribution' to one of the previous listed distributions to configure NVIDIA docker"
	echo "Example:"
	echo "export distribution=ubuntu20.04"
	exit
fi


curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add - && \
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list && \
apt-get update && apt-get install -y nvidia-container-runtime
cat <<EOF | tee /etc/docker/daemon.json
{
	"runtimes": {
		"nvidia": {
			"path": "nvidia-container-runtime",
			"runtimeArgs": []
		}
	},
	"default-runtime": "nvidia",
	"node-generic-resources": [
		"gpu=${GPU_ID}"
	]
}
EOF

cat <<EOF | tee /etc/nvidia-container-runtime/config.toml
swarm-resource = "DOCKER_RESOURCE_GPU"
disable-require = false
#swarm-resource = "DOCKER_RESOURCE_GPU"
#accept-nvidia-visible-devices-envvar-when-unprivileged = true
#accept-nvidia-visible-devices-as-volume-mounts = false

[nvidia-container-cli]
#root = "/run/nvidia/driver"
#path = "/usr/bin/nvidia-container-cli"
environment = []
#debug = "/var/log/nvidia-container-toolkit.log"
#ldcache = "/etc/ld.so.cache"
load-kmods = true
#no-cgroups = false
#user = "root:video"
ldconfig = "/sbin/ldconfig"

[nvidia-container-runtime]
#debug = "/var/log/nvidia-container-runtime.log"
EOF

systemctl daemon-reload
sleep 2
systemctl restart docker
echo
echo
echo
echo "---------------------------------------------------------------------------------"
echo "Running nvidia-smi inside docker"
docker run --rm --gpus all ubuntu:18.04 nvidia-smi





