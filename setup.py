from distutils.core import setup
import os

__version__ = os.environ.get('VERSION', 'v0.0.0').replace('v', '')

setup(
    name='ussd_airflow',
    version=os.environ.get('version', __version__),
    packages=['ussd'],
    url='https://github.com/mwaaas/ussd_airflow',
    license='MIT',
    author='Mwas',
    author_email='mwasgize@gmail.com',
    description='Ussd Airflow Library'
)
