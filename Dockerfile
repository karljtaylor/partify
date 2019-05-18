FROM python:3.7-stretch

ADD . /app

WORKDIR /app

RUN pip install pipenv

RUN pipenv install --system

CMD ["python", "."]
