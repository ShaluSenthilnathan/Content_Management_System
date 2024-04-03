FROM python:3.12

ENV DB_NAME cmsdb
ENV DB_USER postgres
ENV DB_PASSWORD Alsen#211
ENV DB_HOST host.docker.internal
ENV DB_PORT 5432

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]