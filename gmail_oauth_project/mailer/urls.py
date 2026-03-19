from django.urls import path
from . import views

app_name = 'mailer'

urlpatterns = [
    path('',                    views.index,          name='index'),
    path('authorize/',          views.authorize,      name='authorize'),
    path('oauth2/callback/',    views.oauth2_callback, name='oauth2_callback'),
    path('send/',               views.send_email_view, name='send_email'),
    path('send-bulk/',          views.send_bulk_view,  name='send_bulk'),
]