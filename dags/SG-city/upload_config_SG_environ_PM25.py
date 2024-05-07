import sys

sys.path.append("/opt/airflow/dags/SG-city/")
from upload_config_SG_environ import create_dag
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import timezone, timedelta, datetime


dag = create_dag(
    name="PM25",
    start_date=(2024, 5, 7, 17, 30, 0),
    schedule_interval="25 * * * *",
)
