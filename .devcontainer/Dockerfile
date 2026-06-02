# Mastering Agentic AI Certification — dev container image
# Debian-based Python image maintained by the Dev Containers team.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The base image ships a Yarn apt repo whose signing key has expired, which
# breaks `apt-get update`. We don't need Yarn for a Python course, so drop that
# source list (and the Node/yarn one if present) before updating.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/*yarn* 2>/dev/null; true

# System packages commonly needed by agentic AI tooling (graphviz for agent
# graph visualisation, build tools for native wheels, etc.).
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        build-essential \
        graphviz \
        curl \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Keep pip current so newer SDK wheels resolve cleanly.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /workspaces
