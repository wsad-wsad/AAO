#!/bin/sh
/app/main_go &
uvicorn main:fast_app --host 0.0.0.0 --port 8080 --reload