# 1. Base Image
FROM python:3.10-slim

# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_NO_INTERACTION 1

# 3. Install git and poetry
RUN apt-get update && apt-get install -y git \
    && pip install "poetry==1.7.1"

# 4. Set Workdir
WORKDIR /app

# 5. Install Dependencies
# Copy only files needed for installation to leverage Docker cache
COPY pyproject.toml poetry.lock* ./
# Install dependencies, including git-based ones
RUN poetry install --no-root --no-dev

# 6. Copy Application Code
COPY . .

# 7. Expose Port
EXPOSE 8000

# 8. Run Application
CMD ["poetry", "run", "uvicorn", "flock_gitlab.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
