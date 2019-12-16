from backend import settings
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from graphene_django import DjangoObjectType
from graphql_jwt.utils import jwt_payload, jwt_encode, jwt_decode
from jwt.exceptions import ExpiredSignatureError

import graphene
import sys


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class UserActionEnum(graphene.Enum):
    ACTIVATE_USER = "Activate_user"
    UPDATE_EMAIL = "Update_email"
    RESET_PASSWORD = "Reset_password"


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception(settings.USER_NOT_LOGGED_IN_ERROR)

        return user

    def resolve_users(self, info):
        return get_user_model().objects.all()


class SendVerificationEmail(graphene.Mutation):
    user = graphene.String()
    email = graphene.String()
    action = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        email = graphene.String()

        # action=ACTIVATE_USER => To activate a new user
        # action=UPDATE_EMAIL => To change email (User must be active)
        # action=RESET_PASSWORD => To reset password (User must be active)
        action = graphene.Argument(UserActionEnum,
                                   description="Possible values: ACTIVATE_USER, UPDATE_EMAIL or RESET_PASSWORD")

    def mutate(self, info, email, action):

        username = None
        # result = settings.EMAIL_NOT_SENT_ERROR
        result = settings.KO
        errors_list = []

        if email is None or len(email.strip()) == 0:
            errors_list.append(settings.EMAIL_REQUIRED_ERROR)

        user = None
        try:
            user_email = email
            if UserActionEnum.UPDATE_EMAIL == action:
                user = info.context.user
                if user.is_anonymous:
                    raise get_user_model().DoesNotExist
                else:
                    user_email = user.email
            if email is None or len(email.strip()) == 0:
                errors_list.append(settings.EMAIL_REQUIRED_ERROR)

            user = get_user_model().objects.get(email__iexact=user_email)
        except get_user_model().DoesNotExist:
            errors_list.append(settings.USER_DOES_NOT_EXIST_ERROR)

        template_name = None
        site_dir = None
        subject = None
        if user is not None:
            # https://django-graphql-jwt.domake.io/en/stable/settings.html#pyjwt
            username = user.username
            payload = jwt_payload(user)

            if UserActionEnum.ACTIVATE_USER == action:
                if user.is_active:
                    errors_list.append(settings.USER_ACTIVE_ERROR)
                else:
                    template_name = "registration/verify_account_email.html"
                    subject = settings.SITE_NAME + " - Finalizar registro"
                    site_dir = "account/user-activated"
            elif UserActionEnum.UPDATE_EMAIL == action:
                if not user.is_active:
                    errors_list.append(settings.USER_INACTIVE_ERROR)
                elif get_user_model().objects.filter(email__iexact=email).exists():
                    errors_list.append(settings.EMAIL_ALREADY_REGISTERED_ERROR)
                else:
                    payload['email'] = email
                    template_name = "registration/verify_account_email.html"
                    subject = settings.SITE_NAME + " - Actualizar dirección de correo electrónico"
                    site_dir = "account/email-updated"
            elif UserActionEnum.RESET_PASSWORD == action:
                if not user.is_active:
                    errors_list.append(settings.USER_INACTIVE_ERROR)
                else:
                    template_name = "registration/password_reset_email.html"
                    subject = settings.SITE_NAME + " - Restablecer contraseña"
                    site_dir = "account/reset-password-confirm"
            else:
                errors_list.append('InvalidAction')

            if len(errors_list) == 0:
                token = jwt_encode(payload)
                message = render_to_string(template_name, {
                    "user": user.username,
                    "temp_key": token,
                    "site_url": settings.CLIENT_URL,
                    "site_dir": site_dir,
                    "site_name": settings.SITE_NAME
                })
                email_to_send = EmailMessage(subject, message, to=[email])
                email_to_send.send()

                # It save the token information to allow a only use
                user.is_used_last_token = False
                user.last_token = token
                user.save()
                # result = settings.EMAIL_SENT
                result = settings.OK

        return SendVerificationEmail(user=username, email=email, action=action, result=result, errors=errors_list)


class ActivateUser(graphene.Mutation):
    user = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        token = graphene.String()

    def mutate(self, info, token):
        username = None
        # result = settings.USER_NOT_ACTIVATED_ERROR
        result = settings.KO
        errors_list = []

        if token is None or len(token.strip()) == 0:
            errors_list.append(settings.TOKEN_REQUIRED_ERROR)
        else:
            try:
                payload = jwt_decode(token)
                username = payload.get('username')

                if username is None or len(username.strip()) == 0:
                    raise Exception()

                user = None
                try:
                    user = get_user_model().objects.get(username=username)
                except get_user_model().DoesNotExist:
                    errors_list.append(settings.USER_DOES_NOT_EXIST_ERROR)

                if user is not None:
                    if user.is_active:
                        errors_list.append(settings.USER_ACTIVE_ERROR)
                    elif token != user.last_token:
                        raise Exception(settings.TOKEN_NOT_MATCH_ERROR)
                    elif user.is_used_last_token:
                        errors_list.append(settings.TOKEN_USED_ERROR)

                    if len(errors_list) == 0:
                        user.is_active = True
                        user.is_used_last_token = True
                        user.save()

                        # result = settings.USER_ACTIVATED
                        result = settings.OK

            except ExpiredSignatureError:
                errors_list.append(settings.EXPIRED_TOKEN_ERROR)
            except Exception:
                errors_list.append(settings.TOKEN_ERROR)

        return ActivateUser(user=username, result=result, errors=errors_list)


class UpdateEmail(graphene.Mutation):
    user = graphene.String()
    old_email = graphene.String()
    new_email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        token = graphene.String()

    def mutate(self, info, token):
        username = None
        old_email = None
        new_email = None
        # result = settings.EMAIL_NOT_UPDATED_ERROR
        result = settings.KO
        errors_list = []

        if token is None or len(token.strip()) == 0:
            errors_list.append(settings.TOKEN_REQUIRED_ERROR)
        else:
            try:
                payload = jwt_decode(token)
                username = payload.get('username')
                new_email = payload.get('email')

                if username is None or len(username.strip()) == 0 \
                        or new_email is None or len(new_email.strip()) == 0 is None:
                    raise Exception()

                user = None
                try:
                    user = get_user_model().objects.get(username=username)
                    old_email = user.email
                except get_user_model().DoesNotExist:
                    errors_list.append(settings.USER_DOES_NOT_EXIST_ERROR)

                if user is not None:
                    if not user.is_active:
                        errors_list.append(settings.USER_INACTIVE_ERROR)
                    elif token != user.last_token:
                        errors_list.append(settings.TOKEN_NOT_MATCH_ERROR)
                    elif user.is_used_last_token:
                        errors_list.append(settings.TOKEN_USED_ERROR)

                    if len(errors_list) == 0:
                        user.email = new_email.lower()
                        user.is_used_last_token = True
                        user.save()

                        # result = settings.EMAIL_UPDATED
                        result = settings.OK

            except ExpiredSignatureError:
                errors_list.append(settings.EXPIRED_TOKEN_ERROR)
            except Exception:
                errors_list.append(settings.TOKEN_ERROR)

        return UpdateEmail(user=username, old_email=old_email, new_email=new_email, result=result, errors=errors_list)


class ResetPassword(graphene.Mutation):
    user = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        token = graphene.String()
        password1 = graphene.String()
        password2 = graphene.String()

    def mutate(self, info, token, password1, password2):
        username = None
        # result = settings.PASSWORD_NOT_RESET_ERROR
        result = settings.KO
        errors_list = []

        if password1 is None or len(password1.strip()) == 0:
            errors_list.append(settings.PASSWORD1_REQUIRED_ERROR)

        if password2 is None or len(password2.strip()) == 0:
            errors_list.append(settings.PASSWORD2_REQUIRED_ERROR)
        else:
            if password1 != password2:
                errors_list.append(settings.PASSWORDS_NOT_MATCH_ERROR)

        if token is None or len(token.strip()) == 0:
            errors_list.append(settings.TOKEN_REQUIRED_ERROR)
        else:
            try:
                payload = jwt_decode(token)
                username = payload.get('username')
                if username is None or len(username.strip()) == 0:
                    raise Exception()

                user = None
                try:
                    user = get_user_model().objects.get(username=username)
                except get_user_model().DoesNotExist:
                    errors_list.append(settings.USER_DOES_NOT_EXIST_ERROR)

                if user is not None:
                    if not user.is_active:
                        errors_list.append(settings.USER_INACTIVE_ERROR)
                    elif token != user.last_token:
                        errors_list.append(settings.TOKEN_NOT_MATCH_ERROR)
                    elif user.is_used_last_token:
                        errors_list.append(settings.TOKEN_USED_ERROR)

                    if len(errors_list) == 0:
                        # https://django-graphql-jwt.domake.io/en/stable/settings.html#pyjwt
                        username = user.username
                        user.set_password(password1)
                        user.is_used_last_token = True
                        user.save()

                        # result = settings.PASSWORD_RESET
                        result = settings.OK

            except ExpiredSignatureError:
                errors_list.append(settings.EXPIRED_TOKEN_ERROR)
            except Exception:
                errors_list.append(settings.TOKEN_ERROR)

        return ResetPassword(user=username, result=result, errors=errors_list)


class UserInput(graphene.InputObjectType):
    email = graphene.String()
    password1 = graphene.String()
    password2 = graphene.String()
    name = graphene.String()
    surnames = graphene.String()
    phone_number = graphene.String()


class CreateUser(graphene.Mutation):
    email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        input = graphene.Argument(UserInput)

    # def mutate(self, info, username, password, email):
    def mutate(self, info, input):
        result = settings.KO
        errors_list = []

        email = input.email
        password1 = input.password1
        password2 = input.password2
        name = input.name
        surnames = input.surnames
        phone_number = input.phone_number

        if email is None or len(email.strip()) == 0:
            errors_list.append(settings.EMAIL_REQUIRED_ERROR)
        elif get_user_model().objects.filter(email__iexact=email).exists():
            errors_list.append(settings.EMAIL_ALREADY_REGISTERED_ERROR)

        if password1 is None or len(password1.strip()) == 0:
            errors_list.append(settings.PASSWORD1_REQUIRED_ERROR)

        if password2 is None or len(password2.strip()) == 0:
            errors_list.append(settings.PASSWORD2_REQUIRED_ERROR)
        else:
            if password1 != password2:
                errors_list.append(settings.PASSWORDS_NOT_MATCH_ERROR)

        if name is None or len(name.strip()) == 0:
            errors_list.append(settings.NAME_REQUIRED_ERROR)

        if surnames is None or len(surnames.strip()) == 0:
            errors_list.append(settings.SURNAMES_REQUIRED_ERROR)

        if len(errors_list) == 0:
            user = get_user_model()(
                email=email.lower(),
                first_name=name,
                last_name=surnames,
                phone_number=phone_number
            )
            user.set_password(input.password1)
            user.save()

            result = settings.OK

        return CreateUser(email=input.email, result=result, errors=errors_list)


class DeactivateUser(graphene.Mutation):
    user = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info):
        # result = settings.USER_DEACTIVATED_ERROR
        result = settings.KO
        errors_list = []

        user = info.context.user
        if user.is_anonymous:
            errors_list.append(settings.USER_NOT_LOGGED_IN_ERROR)
        elif not user.is_active:
            errors_list.append(settings.USER_INACTIVE_ERROR)

        if len(errors_list) == 0:
            user.is_active = False
            user.save()

            user.is_used_last_token = True
            user.save()
            # result = settings.USER_DEACTIVATED
            result = settings.OK

        return DeactivateUser(user=user.username, result=result, errors=errors_list)


class Mutation(graphene.ObjectType):
    send_verification_email = SendVerificationEmail.Field()
    activate_user = ActivateUser.Field()
    update_email = UpdateEmail.Field()
    reset_password = ResetPassword.Field()
    create_user = CreateUser.Field()
    deactivate_user = DeactivateUser.Field()
