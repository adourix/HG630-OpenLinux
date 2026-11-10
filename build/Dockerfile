FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      ca-certificates file git make python3 python3-minimal \
      binutils binutils-arm-linux-gnueabi \
      gcc-arm-linux-gnueabi g++-arm-linux-gnueabi libc6-dev-armel-cross \
      gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf libc6-dev-armhf-cross \
      squashfs-tools xz-utils lzma \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY tools/ /workspace/tools/
COPY tests/ /workspace/tests/
RUN python3 -m unittest discover -s tests -v

CMD ["bash"]
