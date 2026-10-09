FROM jenkins/jenkins:lts
USER root

# Installer Python 3, pip et curl
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Versions figées pour kube-linter et kube-score (Correction #2)
ARG KUBELINTER_VERSION=0.7.1
ARG KUBESCORE_VERSION=1.20.0

# Télécharger et installer kube-linter
RUN curl -L \
  "https://github.com/stackrox/kube-linter/releases/download/v${KUBELINTER_VERSION}/kube-linter-linux.tar.gz" \
  -o /tmp/kube-linter.tar.gz && \
  tar -xzf /tmp/kube-linter.tar.gz -C /usr/local/bin kube-linter && \
  rm /tmp/kube-linter.tar.gz

# Télécharger et installer kube-score
RUN curl -L \
  "https://github.com/zegl/kube-score/releases/download/v${KUBESCORE_VERSION}/kube-score_${KUBESCORE_VERSION}_linux_amd64.tar.gz" \
  -o /tmp/kube-score.tar.gz && \
  tar -xzf /tmp/kube-score.tar.gz -C /usr/local/bin && \
  chmod +x /usr/local/bin/kube-score && \
  rm /tmp/kube-score.tar.gz

# Installer les bibliothèques Python requises (avec python-dotenv ajouté !)
RUN pip3 install --no-cache-dir openai requests PyYAML tenacity python-dotenv --break-system-packages

USER jenkins
