# syntax=docker/dockerfile:1

FROM ubuntu:20.04
WORKDIR /bot

RUN apt-get update && apt-get install -y \
    python3-pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python3", "bot/impl_bot.py", "--host=0.0.0.0"]