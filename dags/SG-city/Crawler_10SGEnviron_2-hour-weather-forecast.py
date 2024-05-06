import sys

sys.path.append("/opt/airflow/dags/SG-city/")
from Crawler_10SGEnviron import create_dag
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import timezone, timedelta, datetime


dag = create_dag(
    name="2-hour-weather-forecast",
    start_date=(2024, 5, 3, 0, 0, 0),
    schedule_interval="*/30 * * * *",
)
