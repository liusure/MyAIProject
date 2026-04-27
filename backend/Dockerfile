FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --default-timeout=120 -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir .

COPY src/ src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
