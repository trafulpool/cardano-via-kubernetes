FROM python:3.9

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

COPY . .

WORKDIR /app

ENTRYPOINT ["python", "-um", "notify-tip"]
