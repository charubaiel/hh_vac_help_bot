FROM python:3.10-slim


COPY . .

RUN apt-get update && apt-get upgrade
RUN pip install --no-cache-dir --upgrade -r req.txt


CMD ["python3","parser.py"]
