#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" # 获取当前脚本所在目录
IMAGE_REPO="roborts_ros" # 镜像仓库名称
ARCH_TYPE="$(arch)" # 架构类型
ROS_VERSION="noetic" # ROS版本
if [ $ARCH_TYPE == "x86_64" -o ${ARCH_TYPE} == "aarch64" ] # 判断架构类型
then
    IMAGE_TAG="roborts_base_${ARCH_TYPE}" # 镜像标签
    if [ $ARCH_TYPE == "x86_64" ] # 根据架构类型选择基础镜像
    then
        BASE_IMAGE="ubuntu:20.04"
    else
        BASE_IMAGE="nvcr.io/nvidia/l4t-jetpack:r35.4.1"
    fi
else
    # echo "ARCH_TYPE $ARCH_TYPE is supported. Valid architecture is [aarch64, x86_64]"
    # exit 1
    # 我们车上的架构是aarch64，所以这里直接默认使用aarch64
    IMAGE_TAG="roborts_base_aarch64"
    BASE_IMAGE="nvcr.io/nvidia/l4t-jetpack:r35.4.1"
fi

cd ${DIR}

# 构建镜像
# --build-arg BASE_IMAGE=${BASE_IMAGE} 基础镜像
# -t ${IMAGE_REPO}:${IMAGE_TAG} 镜像名称
# -f Dockerfile 选择Dockerfile
# . 当前目录
sudo docker build \
    --build-arg BASE_IMAGE=${BASE_IMAGE} \
    -t ${IMAGE_REPO}:${IMAGE_TAG} \
    -f Dockerfile .