FROM mcr.microsoft.com/dotnet/sdk:8.0
RUN apt-get update && apt-get install -y python3 python3-pip --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY . /app
WORKDIR /app
RUN pip install --break-system-packages .
WORKDIR /workspace
ENTRYPOINT ["amtcz-mcp"]
