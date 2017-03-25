from django.conf.urls import url
from ussd.views import journey_visual,journey_visual_data

urlpatterns = [
    url(r'ussd-airflow/journey_visual$',journey_visual,name="journey_visual"),
    url(r'ussd-airflow/journey_visual_data$',journey_visual_data,name='journey_visual_data')
]
