test:
	@docker-compose run --service-port app python manage.py test

base_image:
	docker build -t  mwaaas/django_ussd_airflow:base_image -f BaseDockerfile .
	docker push mwaaas/django_ussd_airflow:base_image

compile_documentation:
	docker-compose run app make -C /usr/src/app/docs html