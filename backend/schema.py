from dates import schema as dates_schemas
from users import schema as users_schemas

import graphene
import graphql_jwt


class Query(dates_schemas.Query, users_schemas.Query, graphene.ObjectType):
    class Meta:
        description = 'The project root query definition'


class Mutation(dates_schemas.Mutation, users_schemas.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.relay.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.relay.Verify.Field()
    refresh_token = graphql_jwt.relay.Refresh.Field()

    # Long running refresh tokens
    revoke_token = graphql_jwt.relay.Revoke.Field()

    class Meta:
        description = 'The project root mutation definition'


class Subscription(dates_schemas.Subscription, graphene.ObjectType):
    class Meta:
        description = 'The project root subscription definition'


graphql_schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription)
