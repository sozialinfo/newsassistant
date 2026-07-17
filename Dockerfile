FROM odoo:18.0
USER root
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /mnt/oca && \
    git clone --depth 1 --branch 18.0 https://github.com/OCA/queue.git /mnt/oca/queue && \
    git clone --depth 1 --branch 18.0 https://github.com/OCA/web.git /mnt/oca/web
USER odoo