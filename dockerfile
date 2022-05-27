FROM python:3.10-slim-bullseye


COPY utils/req.txt req.txt

ENV DAGSTER_HOME=/opt/dagster/dagster_home/
RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app
RUN touch /opt/dagster/dagster_home/dagster.yaml 
# RUN apt-get update && apt-get upgrade -y

RUN pip install --no-cache-dir --upgrade -r req.txt

WORKDIR /opt/dagster/app

COPY . .

EXPOSE 3000


CMD ["/bin/bash","-c","dagit -h 0.0.0.0 -p 3000 & dagster-daemon run"]