from setuptools import setup, find_packages

__version__ = '0.0.1.5'

setup(
    name='ussd_airflow',
    version=__version__,
    packages=find_packages(exclude=('ussd_airflow',)),
    url='https://github.com/mwaaas/ussd_airflow',
    license='MIT',
    author='Mwas',
    author_email='mwasgize@gmail.com',
    description='Ussd Airflow Library'
)
