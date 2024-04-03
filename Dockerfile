FROM python:3.12

WORKDIR /app

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client

# Copy your application code into the container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Set environment variables for PostgreSQL
ENV POSTGRES_DB=cmsdb
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=Alsen#211
# Use the host machine's IP address for PostgreSQL host
ENV POSTGRES_HOST=host.docker.internal
ENV POSTGRES_PORT=5432

# Command to create database and tables and then run the application
CMD python -c "import psycopg2; \
    conn = psycopg2.connect(dbname='$POSTGRES_DB', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', host='$POSTGRES_HOST', port='$POSTGRES_PORT'); \
    cursor = conn.cursor(); \
    cursor.execute('CREATE TABLE IF NOT EXISTS USERS(ID SERIAL PRIMARY KEY, USERNAME TEXT, PASSWORD TEXT)'); \
    cursor.execute('CREATE TABLE IF NOT EXISTS ARTICLES(ID SERIAL PRIMARY KEY, TITLE TEXT, CONTENT TEXT, AUTHOR_ID INTEGER REFERENCES USERS(ID))'); \
    cursor.execute('CREATE TABLE IF NOT EXISTS COMMENTS(ID SERIAL PRIMARY KEY, TITLE TEXT, CONTENT TEXT, AUTHOR_ID INTEGER REFERENCES USERS(ID))'); \
    conn.commit(); \
    conn.close(); \
    exec(open('app.py').read())"
