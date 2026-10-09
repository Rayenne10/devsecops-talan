FROM jenkins/jenkins:lts-jdk21
USER root
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends python3 python3-venv curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY scripts/install-scanners.sh /tmp/install-scanners.sh
RUN bash /tmp/install-scanners.sh && rm /tmp/install-scanners.sh
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"
RUN jenkins-plugin-cli --plugins workflow-aggregator git credentials-binding htmlpublisher timestamper
USER jenkins
