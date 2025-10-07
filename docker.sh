#!/bin/bash

# Remove the database data to ensure a fresh start
sudo rm -rf ./db_data

docker compose build
docker compose up