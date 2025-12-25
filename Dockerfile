FROM apache/airflow:2.8.1-python3.11

USER airflow

RUN pip install --no-cache-dir requests==2.31.0
