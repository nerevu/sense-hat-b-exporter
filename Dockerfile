ARG TARGETPLATFORM
ARG BUILDPLATFORM
FROM --platform=$BUILDPLATFORM python:3.12-slim-bookworm AS builder

RUN echo "Running on $BUILDPLATFORM, building for $TARGETPLATFORM" > /log

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y python3 python3-pip
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
FROM python:3.12-slim-bookworm
COPY --from=builder /log /log

RUN groupadd i2c && groupadd gpio && groupadd spi
RUN useradd -ms /bin/bash -g staff -G i2c,gpio,spi,dialout sensehat
RUN usermod -aG i2c,gpio,spi,dialout sensehat
USER sensehat
WORKDIR /home/sensehat

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --chown=sensehat:staff ./sensors ./sensors
COPY --chown=sensehat:staff exporter.py .

CMD ["--bind=0.0.0.0", "--port=9111"]
ENTRYPOINT ["python3", "exporter.py"]
