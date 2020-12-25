FROM python:3.7
LABEL maintainer="Mohamed Radwan"

# Place app in container.
COPY . /opt/www
WORKDIR /opt/www

# Install dependencies.
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn"  , "-b", "0.0.0.0:5000", "runserver:app"]
