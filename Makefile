
test:
	docker-compose run --service-port app python manage.py test

distribute:
	@python setup.py sdist

publish:
	@python setup.py sdist upload


	echo "[pypirc]
          servers = pypi
          [server-login]
          username:$PYPI_USER
          password:$PYPI_PASSWORD" > ~/.pypirc
          python setup.py sdist upload
          python setup.py bdist_wheel upload