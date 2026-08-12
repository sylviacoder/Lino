FROM public.ecr.aws/lambda/python:3.12

COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
COPY src ${LAMBDA_TASK_ROOT}/src

RUN pip install \
    --no-cache-dir \
    --target ${LAMBDA_TASK_ROOT} \
    ${LAMBDA_TASK_ROOT}

COPY data ${LAMBDA_TASK_ROOT}/data

ENV LINO_DATA_DIR=${LAMBDA_TASK_ROOT}/data

CMD ["lino_autocare_copilot.api.handler"]