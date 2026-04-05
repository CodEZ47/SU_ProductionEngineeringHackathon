FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install uv && uv sync

COPY . .

EXPOSE 5000

CMD ["uv", "run", "python", "run.py"]