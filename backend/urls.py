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
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import \
    csrf_exempt  # Only in development (new solution to disable CORS in development)
from graphene_django.views import GraphQLView

import django
import pathlib


# --------------------------------------------------- URL CONFIGURATION (For channels_graphql_ws module - subscriptions)
def graphiql(request):
    """Trivial ad-hoc view to serve the `graphiql.html` file."""
    del request
    graphiql_filepath = pathlib.Path(__file__).absolute().parent / "templates/graphiql.html"
    with open(graphiql_filepath) as f:
        return django.http.response.HttpResponse(f.read())


urlpatterns = [
    # Django admin urls
    path('', include('health_check.urls')),
    path('admin/', admin.site.urls),

    # TODO review URLs
    # Subscriptions only works from this url
    # This url don't returns schema.graphql (Perhaps it was used in wrong way to get it)
    # path("graphiql/", graphiql), # Uncomment in real?
    path("graphiql/", csrf_exempt(graphiql)),
    # path("graphiql/", graphiql),

    # Subscriptions doesn't work from this url
    # This url is used to get schema.graphql
    # path('graphql/', GraphQLView.as_view(graphiql=True)), # Uncomment in real?
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # path('graphql/', GraphQLView.as_view(graphiql=True)),
]
