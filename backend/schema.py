import graphene
import graphql_jwt

from dates import schema as dates_schemas
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import get_token
from users import schema as users_schemas


class Query(dates_schemas.Query, users_schemas.Query, graphene.ObjectType):
    class Meta:
        description = 'The project root query definition'


# This class is created in order to log in with email and password
class CustomObtainJSONWebToken(graphene.Mutation):
    token = graphene.String(required=True)
    user = graphene.Field(users_schemas.UserNode)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, email, password):
        user = get_user_model().objects.filter(email__iexact=email).first()
        if user is None:
            raise Exception('EmailNotExists')
        if not user.check_password(password):
            raise Exception('WrongPassword')
        token = get_token(user)

        return cls(token, user)


class Mutation(dates_schemas.Mutation, users_schemas.Mutation, graphene.ObjectType):
    token_auth = CustomObtainJSONWebToken.Field()
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
