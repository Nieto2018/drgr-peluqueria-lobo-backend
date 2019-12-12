from backend.settings import CLIENT_URL, SITE_NAME
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from graphene_django import DjangoObjectType
from graphql_jwt.utils import jwt_payload, jwt_encode, jwt_decode

import graphene


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class UserActionEnum(graphene.Enum):
    CREATE_USER = "CREATE_USER"
    UPDATE_EMAIL = "UPDATE_EMAIL"
    RESET_PASSWORD = "RESET_PASSWORD"


class SendVerificationEmail(graphene.Mutation):
    user = graphene.String()
    email = graphene.String()
    action = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        email = graphene.String()

        # action=CREATE_USER => To activate a new user
        # action=UPDATE_EMAIL => To change email (User must be active)
        # action=RESET_PASSWORD => To reset password (User must be active)
        action = graphene.Argument(UserActionEnum,
                                   description="Possible values: CREATE_USER, UPDATE_EMAIL or RESET_PASSWORD")

    def mutate(self, info, email, action):

        user = None
        username = None
        errors_list = []
        result = "EmailNotSent"

        if email is None or len(email.strip()) == 0:
            errors_list.append('EmailRequired')
            # raise Exception('EmailRequired')

        try:
            user = get_user_model().objects.get(email__iexact=email)
        except get_user_model().DoesNotExist:
            errors_list.append('UserDoesNotExist')
            # raise Exception('UserDoesNotExist')

        template_name = None
        token = None
        site_dir = None
        subject = None
        if user is not None:
            # https://django-graphql-jwt.domake.io/en/stable/settings.html#pyjwt
            username = user.username
            payload = jwt_payload(user, context=None)
            payload['email'] = email
            token = jwt_encode(payload, context=None)

            if UserActionEnum.CREATE_USER == action:
                if user.is_active:
                    errors_list.append('UserActive')
                    # raise Exception('UserActive')
                template_name = "registration/verify_account_email.html"
                subject = SITE_NAME + " - Finalizar registro"
                site_dir = "account/user-activated"
            else:
                if UserActionEnum.UPDATE_EMAIL == action:
                    if not user.is_active:
                        errors_list.append('UserInactive')
                        # raise Exception('UserInactive')
                    template_name = "registration/verify_account_email.html"
                    subject = SITE_NAME + " - Actualizar dirección de correo electrónico"
                    site_dir = "account/email-updated"
                else:
                    if UserActionEnum.RESET_PASSWORD == action:
                        if not user.is_active:
                            errors_list.append('UserInactive')
                            # raise Exception('UserInactive')
                        template_name = "registration/password_reset_email.html"
                        subject = SITE_NAME + " - Restablecer contraseña"
                        site_dir = "account/reset-password-confirm"
                    else:
                        errors_list.append('InvalidAction')
                        # raise Exception('InvalidAction')

        if len(errors_list) == 0:
            message = render_to_string(template_name, {
                "user": user.username,
                "temp_key": token,
                "site_url": CLIENT_URL,
                "site_dir": site_dir,
                "site_name": SITE_NAME
            })
            email_to_send = EmailMessage(subject, message, to=[email])
            email_to_send.send()
            result = "EmailSent"

        return SendVerificationEmail(user=username, email=email, action=action, result=result, errors=errors_list)


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    # send_verification_email = SendVerificationEmail.Field()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('UserNotLoggedIn')

        return user

    def resolve_users(self, info):
        return get_user_model().objects.all()


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = get_user_model()(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user)


class UpdateEmail(graphene.Mutation):
    user = graphene.String()
    email = graphene.String()
    result = graphene.String()

    class Arguments:
        token = graphene.String(required=True)

    def mutate(self, info, token):
        payload = jwt_decode(token)
        username = payload.get('username')
        email = payload.get('email')

        try:
            user = get_user_model().objects.get(username__iexact=username, is_active=True)
        except get_user_model().DoesNotExist:
            raise Exception('UserDoesNotExist')

        user.email = email
        user.save()

        return UpdateEmail(user=username, email=email, result="EmailUpdated")


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_email = UpdateEmail.Field()
    send_verification_email = SendVerificationEmail.Field()
