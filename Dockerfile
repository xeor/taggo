FROM python:3.6-alpine

RUN pip install taggo

ENTRYPOINT ["taggo"]
