FROM python:3-alpine
RUN mkdir /app
WORKDIR /app
COPY jlrpy.py examples/*py ./

