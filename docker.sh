#!/bin/bash

# Remove the database data to ensure a fresh start
rm -rf ./db_data

docker compose build
docker compose up