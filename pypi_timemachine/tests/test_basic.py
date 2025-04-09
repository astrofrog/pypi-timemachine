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
astropy==7.0.0
astropy-iers-data==0.2024.12.2.0.35.34
numpy==2.1.3
packaging==24.2
pyerfa==2.0.1.5
PyYAML==6.0.2
""".strip()

def test_basic(tmpdir):
    subprocess.check_output([sys.executable, '-m', 'venv', tmpdir])
    with timemachine('2024-12-03T22:12:33'):
        subprocess.check_output([os.path.join(tmpdir, 'bin', 'python'), '-m', 'pip', 'install', '-i', f'http://localhost:8100', 'astropy'])
    freeze_output = subprocess.check_output([os.path.join(tmpdir, 'bin', 'python'), '-m', 'pip', 'freeze'])
    assert freeze_output.decode('utf-8').strip() == BASIC_EXPECTED
