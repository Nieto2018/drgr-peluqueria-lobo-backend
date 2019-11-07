import channels_graphql_ws

from .schema import graphql_schema
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path


# ------------------------------------------ CHANNELS URL CONFIGURATION (For channels_graphql_ws module - subscriptions)
class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    """Channels WebSocket consumer which provides GraphQL API."""

    schema = graphql_schema


# ------------------------------------------------------------------------- ASGI ROUTING
application = ProtocolTypeRouter(
    {
        "websocket": URLRouter(
            [
                # The file graphiql.html should point to the next path for subscriptions
                path("subscriptions/", MyGraphqlWsConsumer)
            ]
        )
    }
)
