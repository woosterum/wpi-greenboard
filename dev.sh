#!/bin/bash

echo "Starting development environment with hot reload..."

# Build and run development containers
docker compose -f compose.dev.yml build
docker compose -f compose.dev.yml up