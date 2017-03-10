from setuptools import setup, find_packages
import os

__version__ = '0.0.3.9.1'


def _strip_comments(l):
    return l.split('#', 1)[0].strip()


def _pip_requirement(req):
    if req.startswith('-r '):
        _, path = req.split()
        return reqs(*path.split('/'))
    return [req]


def _reqs(*f):
    return [
        _pip_requirement(r) for r in (
            _strip_comments(l) for l in open(
                os.path.join(os.getcwd(), *f)).readlines()
        ) if r]


def reqs(*f):
    """Parse requirement file.
    Example:
        reqs('default.txt')          # requirements/default.txt
        reqs('extras', 'redis.txt')  # requirements/extras/redis.txt
    Returns:
        List[str]: list of requirements specified in the file.
    """
    return [req for subreq in _reqs(*f) for req in subreq]

setup(
    name='ussd_airflow',
    version=__version__,
    packages=find_packages(exclude=('ussd_airflow',)),
    url='https://github.com/mwaaas/ussd_airflow',
    install_requires=reqs('default.txt'),
    include_package_data=True,
    license='MIT',
    author='Mwas',
    author_email='mwasgize@gmail.com',
    description='Ussd Airflow Library'
)
