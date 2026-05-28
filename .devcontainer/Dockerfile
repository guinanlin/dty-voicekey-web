# 轻量 Dev Container 工作区：Python 3.12 slim + uv + Bun
ARG PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.12-slim
FROM ${PYTHON_IMAGE}

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        git \
        procps \
        unzip \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:${PATH}"

ENV BUN_INSTALL=/usr/local/bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="${BUN_INSTALL}/bin:${PATH}"

WORKDIR /workspaces/nextjs-fastapi-template
