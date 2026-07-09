# Use standard lightweight python base
FROM python:3.11-slim as builder

WORKDIR /code

# Install system dependencies if any are needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final image stage
FROM python:3.11-slim

WORKDIR /code

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY . /code

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/code

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
