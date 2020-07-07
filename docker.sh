#!/bin/bash
#
# Docker container for tuneit
# Usage: docker.tuneit.test

function docker.tuneit.build() { 
docker build --force-rm --rm --tag=ubuntu:tuneit - << EOF
FROM ubuntu:18.04 
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --fix-missing
RUN apt-get install --yes git vim
RUN apt-get install --yes python3 python3-pip
RUN python3 -m pip install --upgrade pip
RUN git clone https://github.com/sbacchio/tuneit
WORKDIR /tuneit
RUN pip install pytest pytest-cov
RUN pip install .[all]
CMD bash
LABEL description="Ubuntu"
EOF
}
alias docker.tuneit.run='docker run --rm -i -t --name tuneit ubuntu:tuneit ' # interactive shell
alias docker.tuneit.rm='docker image rm ubuntu:tuneit'
alias docker.tuneit.test='docker.tuneit.build && docker.tuneit.run date && docker.tuneit.run pytest'
