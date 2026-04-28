FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --default-timeout=120 -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir .

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
