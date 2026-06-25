FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH="${JAVA_HOME}/bin:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${PATH}"

# Dependencias del sistema
RUN apt-get update -qq && apt-get install -y \
    python3.11 python3.11-dev python3.11-distutils \
    build-essential git zip unzip curl wget \
    openjdk-17-jdk \
    libffi-dev libssl-dev \
    autoconf libtool pkg-config \
    zlib1g-dev cmake \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11 como default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# pip + herramientas
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    python3.11 -m pip install --upgrade pip setuptools wheel

# Cython y buildozer con versiones compatibles con Python 3.11
RUN python3.11 -m pip install \
    cython==3.0.1 \
    buildozer==1.5.0

# Symlinks para que buildozer encuentre los binarios
RUN ln -sf $(python3.11 -c "import sysconfig; print(sysconfig.get_path('scripts'))")/cython /usr/local/bin/cython && \
    ln -sf $(python3.11 -c "import sysconfig; print(sysconfig.get_path('scripts'))")/buildozer /usr/local/bin/buildozer

# Verificar
RUN python3 --version && cython --version && buildozer version

WORKDIR /app
