# 基础镜像
ARG BASE_IMAGE=ros:noetic-ros-base-focal 
FROM ${BASE_IMAGE}

# 安装ROS
RUN apt update \ 
    && apt install wget python3-yaml -y  \
    # 安装noetic
    && echo "chooses:\n" > fish_install.yaml \
    && echo "- {choose: 1, desc: '一键安装:ROS(支持ROS和ROS2,树莓派Jetson)'}\n" >> fish_install.yaml \
    && echo "- {choose: 1, desc: 更换源继续安装}\n" >> fish_install.yaml \
    && echo "- {choose: 2, desc: 清理三方源}\n" >> fish_install.yaml \
    && echo "- {choose: 3, desc: noetic(ROS1)}\n" >> fish_install.yaml \
    && echo "- {choose: 1, desc: noetic(ROS1)桌面版}\n" >> fish_install.yaml \
    && wget http://fishros.com/install  -O fishros && /bin/bash fishros \
    # 进行最后的清理
    && rm -rf /var/lib/apt/lists/*  /tmp/* /var/tmp/* \
    && apt-get clean && apt autoclean 

# 安装ROS依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-tf ros-noetic-nav-msgs ros-noetic-geometry-msgs ros-noetic-rplidar-ros libgoogle-glog-dev python3-pip \
    libopencv-dev python3-opencv \
    && rm -rf /var/lib/apt/lists/*
# 拷贝roborts工作空间和RMUA工作空间
COPY ./RMUA /root/RMUA
COPY ./roborts /root/roborts
COPY ./client.py /root/RMUA/src/sentry/scripts/client.py

# 编译roborts
WORKDIR /root/roborts
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && catkin_make"

# 编译RMUA
WORKDIR /root/RMUA/src
RUN /bin/bash -c "source /root/roborts/devel/setup.bash && \
    catkin_init_workspace && \
    cd vision && \
    pip install -r requirements.txt && \
    cd ../.. && \
    catkin_make --only-pkg-with-deps sentry && \
    catkin_make -DCATKIN_WHITELIST_PACKAGES=\"decision;navigation;vision\""
RUN /bin/bash -c "source /root/RMUA/devel/setup.bash"


CMD ["bash"]