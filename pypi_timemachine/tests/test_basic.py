import os
import sys
import time
import contextlib
import subprocess

@contextlib.contextmanager
def timemachine(date,  port=8100):

    process = subprocess.Popen(
        ['pypi-timemachine',
    date, '--port', str(port)])

    try:
        time.sleep(2)
        yield
    finally:
        process.terminate()
        process.wait()

BASIC_EXPECTED = """
astropy==7.0.1
astropy-iers-data==0.2025.4.7.0.35.30
numpy==2.2.4
packaging==24.2
pyerfa==2.0.1.5
PyYAML==6.0.2
"""

def test_basic(tmpdir):
    subprocess.check_output([sys.executable, '-m', 'venv', tmpdir])
    with timemachine('2023-02-03T22:12:33'):
        subprocess.check_output([os.path.join(tmpdir, 'bin', 'python'), '-m', 'pip', 'install', '-i', f'http://localhost:8100', 'astropy'])
    freeze_output = subprocess.check_output([os.path.join(tmpdir, 'bin', 'python'), '-m', 'pip', 'freeze'])
    assert freeze_output == BASIC_EXPECTED
