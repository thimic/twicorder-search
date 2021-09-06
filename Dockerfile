FROM python:3.9-alpine

ENV TWICORDER_PROJECT_DIR /data
ENV TWICORDER_RUN_TASK_FILE /config/tasks.yaml
ENV TWICORDER_RUN_FULL_USER_MENTIONS false

RUN apk update && apk add gcc libffi-dev musl-dev make libressl-dev

WORKDIR /etc/twicorder

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/twicorder ./src/twicorder
COPY bin ./bin

ENV PYTHONPATH "/etc/twicorder/src"

CMD [ "python", "./bin/twicorder", "run" ]
