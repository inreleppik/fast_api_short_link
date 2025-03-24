FROM python:3.9

WORKDIR /fastapi_short_link

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Эта строка — решение!
ENV PYTHONPATH="${PYTHONPATH}:/fastapi_short_link/src"

RUN chmod +x docker/app.sh
CMD ["bash", "docker/app.sh"]