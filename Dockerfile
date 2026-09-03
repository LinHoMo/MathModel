# MathModelSkills Docker Image
# Provides: Python 3.11 + TeX Live (XeLaTeX) + math modeling packages
#
# Build:  docker build -t mathmodel-skills .
# Run:    docker run -it --rm -v ./projects:/app/projects mathmodel-skills bash
# Compose: docker compose up -d (see docker-compose.yml)

FROM python:3.11-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

FROM base AS latex

RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-chinese \
    texlive-science \
    latexmk \
    biber \
    && rm -rf /var/lib/apt/lists/*

FROM latex AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir numpy scipy pandas matplotlib seaborn \
    scikit-learn xgboost networkx sympy statsmodels openpyxl \
    requests Pillow lxml

COPY . .

RUN pip install --no-cache-dir -e .

RUN python core/tools/doctor.py || true

ENTRYPOINT ["bash"]
