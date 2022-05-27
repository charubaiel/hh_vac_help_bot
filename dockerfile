FROM python:3.10-slim-bullseye

COPY utils/req.txt req.txt

# RUN apt-get update && apt-get upgrade -y

RUN pip install --no-cache-dir --upgrade -r req.txt


RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app


# Copy your code and workspace to /opt/dagster/app

# ENV DAGSTER_HOME=/opt/dagster/dagster_home/

# Copy dagster instance YAML to $DAGSTER_HOME
RUN touch /opt/dagster/dagster_home/dagster.yaml 

WORKDIR /opt/dagster/app

COPY . .

# EXPOSE 3000


# CMD ["/bin/bash","-c","dagit -f parse_pipelines.py -h 0.0.0.0 -p 3000 & dagster-daemon run"]