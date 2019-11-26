"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import django
import pathlib

from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView

# Aunthentication urls (django-rest-auth module)
from django.conf.urls import url
from rest_auth.views import PasswordResetView, PasswordResetConfirmView

# Only in development (new solution to disable CORS in development)
from django.views.decorators.csrf import csrf_exempt


# --------------------------------------------------- URL CONFIGURATION (For channels_graphql_ws module - subscriptions)
def graphiql(request):
    """Trivial ad-hoc view to serve the `graphiql.html` file."""
    del request
    graphiql_filepath = pathlib.Path(__file__).absolute().parent / "templates/graphiql.html"
    with open(graphiql_filepath) as f:
        return django.http.response.HttpResponse(f.read())


urlpatterns = [
    # Django admin urls
    path('admin/', admin.site.urls),

    # Subscriptions only works from this url
    # This url don't returns schema.graphql (Perhaps it was used in wrong way to get it)
    # path("graphiql/", graphiql), # Uncomment in real?
    path("graphiql/", csrf_exempt(graphiql)),

    # Subscriptions doesn't work from this url
    # This url is used to get schema.graphql
    # path('graphql/', GraphQLView.as_view(graphiql=True)), # Uncomment in real?
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),

    # Aunthentication urls (django-rest-auth module)
    url('rest-auth/password/reset/$', PasswordResetView.as_view(), name='rest_password_reset'),
    url('rest-auth/password/reset/confirm/$', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
]
