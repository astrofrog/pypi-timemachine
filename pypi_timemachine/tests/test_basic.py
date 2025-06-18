import os
import sys
import time
import contextlib
import subprocess
import typing


@contextlib.contextmanager
def timemachine(date: str, port: int = 8100, extra_args: typing.Iterable[str] = ()):
    process = subprocess.Popen(
        ["pypi-timemachine", date, "--port", str(port)] + list(extra_args)
    )

    try:
        time.sleep(2)
        yield
    finally:
        process.terminate()
        process.wait()


BASIC_DATE = "2024-12-03T22:12:33Z"
BASIC_EXPECTED = """
astropy==7.0.0
astropy-iers-data==0.2024.12.2.0.35.34
numpy==2.1.3
packaging==24.2
pyerfa==2.0.1.5
PyYAML==6.0.2
"""


def test_basic(tmpdir):
    subprocess.check_output([sys.executable, "-m", "venv", tmpdir])
    python_executable = os.path.join(
        tmpdir,
        "Scripts" if os.name == "nt" else "bin",
        "python",
    )
    with timemachine(BASIC_DATE):
        subprocess.check_output(
            [
                python_executable,
                "-m",
                "pip",
                "install",
                "-i",
                "http://localhost:8100",
                "astropy",
            ]
        )
    freeze_output = subprocess.check_output([python_executable, "-m", "pip", "freeze"])
    assert (
        freeze_output.decode("utf-8").strip().splitlines()
        == BASIC_EXPECTED.strip().splitlines()
    )


def test_custom_index_url(tmpdir):
    subprocess.check_output([sys.executable, "-m", "venv", tmpdir])
    python_executable = os.path.join(
        tmpdir,
        "Scripts" if os.name == "nt" else "bin",
        "python",
    )
    with timemachine("2900-01-01"):
        with timemachine(
            "2900-01-01",
            port=8101,
            extra_args=["--index-url", f"http://localhost:8100/snapshot/{BASIC_DATE}"],
        ):
            subprocess.check_output(
                [
                    python_executable,
                    "-m",
                    "pip",
                    "install",
                    "-i",
                    "http://localhost:8101",
                    "astropy",
                ]
            )
    freeze_output = subprocess.check_output([python_executable, "-m", "pip", "freeze"])
    assert (
        freeze_output.decode("utf-8").strip().splitlines()
        == BASIC_EXPECTED.strip().splitlines()
    )
