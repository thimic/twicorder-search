FROM python:3.8-alpine

ENV TWICORDER_PROJECT_DIR /data
ENV TWICORDER_RUN_TASK_FILE /config/tasks.yaml
ENV TWICORDER_RUN_FULL_USER_MENTIONS true

RUN apk update && apk add gcc libffi-dev musl-dev make libressl-dev

WORKDIR /etc/twicorder

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY twicorder ./pylib/twicorder
COPY bin ./bin

ENV PYTHONPATH "/etc/twicorder/pylib"

CMD [ "python", "./bin/twicorder", "run" ]
