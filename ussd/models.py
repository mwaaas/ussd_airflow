from django.db import models


class SessionLookup(models.Model):
    """
    This model is used by built in session management 
    to map between user_id and session_id
    """
    user_id = models.CharField(max_length=255)  # this can also be phone number
    session_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(u'Creation Date', auto_now=True)
    updated_at = models.DateTimeField(u'Update Date', auto_now_add=True)
