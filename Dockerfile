FROM python:3.9

RUN apt-get update && apt-get install -y netcat-openbsd

RUN mkdir /fast_api_short_link
WORKDIR /fast_api_short_link

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh