FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY driver_router/ driver_router/
# Beside the module, where device_info.py looks first (a checkout run uses the repo-root file).
COPY manifest.json driver_router/manifest.json

# The release workflow passes the git release tag. Unset (a local build) reports "dev".
ARG DEVICE_VERSION
ENV DEVICE_VERSION=${DEVICE_VERSION}

ENTRYPOINT ["python", "-m", "driver_router.main"]
