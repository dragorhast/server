#!/usr/bin/env bash

if [[ "$DATABASE_URL" == "postgres://postgres:@127.0.0.1:5432/travis_ci_test" ]]; then
    psql -U postgres -c 'create database travis_ci_test;'
    psql -U postgres -c 'create extension postgis;'
fi
