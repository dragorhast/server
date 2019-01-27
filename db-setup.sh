#!/usr/bin/env bash

if [[ "$DATABASE_URL" == "postgres://postgres:@127.0.0.1:5432/test" ]]; then
    psql -c 'create database test;' -U postgres
    psql -c 'CREATE EXTENSION postgis;' -U postgres -d test
fi