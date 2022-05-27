#!/bin/bash

if [[ $(docker ps -a | grep -w "hh_parse"_container) ]]; then docker stop "hh_parse"_container && docker rm "hh_parse"_container; fi

if [[ $(docker images | grep -w "hh_parse") ]]; then docker rmi "hh_parse"; fi

docker build -t hh_parse .

docker run --name hh_parse_container\
            -d \
            -p 3000:3000 \
            -v $(pwd)/data:/opt/dagster/app/data \
            hh_parse