FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock requirements.txt ./

RUN pip install uv && uv sync --locked

COPY . .

EXPOSE 5000

CMD ["uv", "run", "python", "run.py"]