# Dockerfile (Wersja finalna)

FROM debian:bullseye-slim

ARG USER_ID=1000
ARG GROUP_ID=1000
ENV DEBIAN_FRONTEND=noninteractive

ARG TOOLCHAIN_VERSION=13.2.rel1
ARG TOOLCHAIN_URL=https://developer.arm.com/-/media/Files/downloads/gnu/13.2.rel1/binrel/arm-gnu-toolchain-13.2.rel1-x86_64-arm-none-eabi.tar.xz

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-pip \
    ninja-build \
    wget \
    xz-utils \
    git \
    sudo && \
    # Pobierz i rozpakuj toolchain do /opt/toolchain
    mkdir -p /opt/toolchain && \
    wget -qO- "${TOOLCHAIN_URL}" | tar -xJ -C /opt/toolchain --strip-components=1 && \
    pip3 install meson && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Dodajemy toolchain do PATH dla wygody, ale nie będziemy na tym polegać w Meson
ENV PATH="/opt/toolchain/bin:${PATH}"

RUN groupadd --gid $GROUP_ID builder && \
    useradd --uid $USER_ID --gid $GROUP_ID -m -s /bin/bash builder && \
    echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER builder
WORKDIR /app

CMD [ "/bin/bash" ]