import sys

sys.path.append("/opt/airflow/dags/SG-city/")
from Crawler_10SGEnviron import create_dag
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import timezone, timedelta, datetime


dag = create_dag(
    name="4-day-weather-forecast",
    start_date=(2024, 5, 6, 15, 30, 0),
    schedule_interval="26 5,17 * * *",
)
