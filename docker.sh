#!/bin/bash
#
# Docker container for tunable
# Usage: docker.tunable.test

function docker.tunable.build() { 
docker build --force-rm --rm --tag=ubuntu:tunable - << EOF
FROM ubuntu:18.04 
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --fix-missing
RUN apt-get install --yes git vim
RUN apt-get install --yes python3 python3-pip
RUN python3 -m pip install --upgrade pip
RUN git clone https://github.com/sbacchio/tunable
WORKDIR /tunable
RUN pip install pytest pytest-cov
RUN pip install .[all]
CMD bash
LABEL description="Ubuntu"
EOF
}
alias docker.tunable.run='docker run --rm -i -t --name tunable ubuntu:tunable ' # interactive shell
alias docker.tunable.rm='docker image rm ubuntu:tunable'
alias docker.tunable.test='docker.tunable.build && docker.tunable.run date && docker.tunable.run pytest'
