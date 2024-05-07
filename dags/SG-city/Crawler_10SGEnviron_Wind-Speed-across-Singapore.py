import sys

sys.path.append("/opt/airflow/dags/SG-city/")
from Crawler_10SGEnviron import create_dag
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import timezone, timedelta, datetime


dag = create_dag(
    name="Wind-Speed-across-Singapore",
    start_date=(2024, 5, 6, 17, 45, 0),
    schedule_interval="*/10 * * * *",
)
