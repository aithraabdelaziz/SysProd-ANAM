import subprocess
from datetime import date
from celery import shared_task
from jobs import config

@shared_task
def run_fctwise_all_ranges():
    today = date.today().strftime("%Y-%m-%d")
    ranges = [(12, 36),(12, 24), (24, 36), (36, 48), (48, 60)]
    log_file = f"{config.LOG_DIR}/fctwise.txt"

    with open(log_file, "a") as f:
        for r in ranges:
            cmd = [
                config.PYTHON_BIN,
                config.MANAGE_PY,
                "fctwise",
                f"--date={today}",
                f"--from={r[0]}",
                f"--to={r[1]}"
            ]
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)


@shared_task
def run_grib_script():
    script_path = "/home/anam/sysprod-project/jobs/models/grib/gfs-25/grib.py"
    log_file = f"{config.LOG_DIR}/gfs.txt"

    with open(log_file, "a") as f:
        subprocess.run(
            [config.PYTHON_BIN, script_path],
            stdout=f,
            stderr=subprocess.STDOUT
        )

@shared_task
def vigilance_calcul():
    script_path = "/home/anam/sysprod-project/jobs/models/vigimet/calcul.py"
    log_file = f"{config.LOG_DIR}/vigilance.txt"

    with open(log_file, "a") as f:
        subprocess.run(
            [config.PYTHON_BIN, script_path],
            stdout=f,
            stderr=subprocess.STDOUT
        )

