from backend import settings
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from graphene_django import DjangoObjectType
from graphql_jwt.utils import jwt_payload, jwt_encode, jwt_decode
from jwt.exceptions import ExpiredSignatureError

import datetime
import graphene
import phonenumbers
import re
import sys


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class AccountActionEnum(graphene.Enum):
    ACTIVATE_ACCOUNT = "Activate_account"
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
    email = graphene.String()
    action = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        email = graphene.String()

        # action=ACTIVATE_ACCOUNT => To activate a new account
        # action=UPDATE_EMAIL => To change email (Account must be active)
        # action=RESET_PASSWORD => To reset password (Account must be active)
        action = graphene.Argument(AccountActionEnum,
                                   description="Possible values: ACTIVATE_ACCOUNT, UPDATE_EMAIL or RESET_PASSWORD")

    def mutate(self, info, email, action):
        user_email = None
        # result = settings.EMAIL_NOT_SENT_ERROR
        result = settings.KO
        errors_list = []

        user = None
        email_pattern = re.compile(settings.EMAIL_REGEX_PATTERN)
        if email is None or len(email.strip()) == 0:
            errors_list.append(settings.EMAIL_REQUIRED_ERROR)
        elif email_pattern.match(email) is None:
            errors_list.append(settings.EMAIL_REGEX_ERROR)
        elif AccountActionEnum.UPDATE_EMAIL == action:
            context_user = info.context.user
            if context_user.is_anonymous:
                errors_list.append(settings.USER_NOT_LOGGED_IN_ERROR)
            elif get_user_model().objects.filter(email__iexact=email).exists():
                errors_list.append(settings.EMAIL_ALREADY_REGISTERED_ERROR)
            else:
                user = context_user
        else:
            try:
                user = get_user_model().objects.get(email__iexact=email)
            except get_user_model().DoesNotExist:
                errors_list.append(settings.ACCOUNT_DOES_NOT_EXIST_ERROR)

        template_name = None
        site_dir = None
        subject = None
        if user is not None:
            # https://django-graphql-jwt.domake.io/en/stable/settings.html#pyjwt
            payload = jwt_payload(user)
            payload['exp'] = datetime.datetime.utcnow() + settings.JWT_EXPIRATION_DELTA_EMAILS

            if AccountActionEnum.ACTIVATE_ACCOUNT == action:
                if user.is_active:
                    errors_list.append(settings.ACCOUNT_ACTIVE_ERROR)
                else:
                    template_name = "registration/verify_account_email.html"
                    subject = settings.SITE_NAME + " - Finalizar registro"
                    site_dir = "account/activate-account"
            elif AccountActionEnum.UPDATE_EMAIL == action:
                if not user.is_active:
                    errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)
                else:
                    payload['new_email'] = email
                    template_name = "registration/verify_account_email.html"
                    subject = settings.SITE_NAME + " - Actualizar dirección de correo electrónico"
                    site_dir = "account/update-email"
            elif AccountActionEnum.RESET_PASSWORD == action:
                if not user.is_active:
                    errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)
                else:
                    template_name = "registration/password_reset_email.html"
                    subject = settings.SITE_NAME + " - Restablecer contraseña"
                    site_dir = "account/reset-password-confirm"
            else:
                errors_list.append('InvalidAction')

            if len(errors_list) == 0:
                token = jwt_encode(payload)
                message = render_to_string(template_name, {
                    "user": user.first_name,
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

        return SendVerificationEmail(email=user_email, action=action, result=result, errors=errors_list)


class CreateAccountInput(graphene.InputObjectType):
    email = graphene.String()
    password1 = graphene.String()
    password2 = graphene.String()
    name = graphene.String()
    surnames = graphene.String()
    phone_number = graphene.String()


class CreateAccount(graphene.Mutation):
    email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        input = graphene.Argument(CreateAccountInput)

    def mutate(self, info, input):
        result = settings.KO
        errors_list = []

        email = input.email
        password1 = input.password1
        password2 = input.password2
        name = input.name
        surnames = input.surnames
        phone_number = input.phone_number

        email_pattern = re.compile(settings.EMAIL_REGEX_PATTERN)
        if email is None or len(email.strip()) == 0:
            errors_list.append(settings.EMAIL_REQUIRED_ERROR)
        elif email_pattern.match(email) is None:
            errors_list.append(settings.EMAIL_REGEX_ERROR)
        elif get_user_model().objects.filter(email__iexact=email).exists():
            errors_list.append(settings.EMAIL_ALREADY_REGISTERED_ERROR)

        if password1 is None or len(password1.strip()) == 0:
            errors_list.append(settings.PASSWORD1_REQUIRED_ERROR)

        if password2 is None or len(password2.strip()) == 0:
            errors_list.append(settings.PASSWORD2_REQUIRED_ERROR)

        if password1 != password2:
            errors_list.append(settings.PASSWORDS_NOT_MATCH_ERROR)
        else:
            password_pattern = re.compile(settings.PASSWORD_REGEX_PATTERN)
            if password_pattern.match(password1) is None:
                errors_list.append(settings.PASSWORD_REGEX_ERROR)

        if name is None or len(name.strip()) == 0:
            errors_list.append(settings.NAME_REQUIRED_ERROR)

        if surnames is None or len(surnames.strip()) == 0:
            errors_list.append(settings.SURNAMES_REQUIRED_ERROR)

        if phone_number is None or len(phone_number.strip()) == 0:
            errors_list.append(settings.PHONE_NUMBER_REQUIRED_ERROR)
        else:
            try:
                parsed_phone_number = phonenumbers.parse(phone_number)
                if not phonenumbers.is_valid_number(parsed_phone_number):
                    errors_list.append(settings.PHONE_NUMBER_NOT_VALID_ERROR)
            except phonenumbers.NumberParseException:
                errors_list.append(settings.PHONE_NUMBER_NOT_VALID_ERROR)

        if len(errors_list) == 0:
            user = get_user_model()(
                email=email.lower(),
                first_name=name,
                last_name=surnames,
                phone_number=phone_number
            )
            user.set_password(input.password1)
            user.is_active = False
            user.save()

            result = settings.OK

        return CreateAccount(email=input.email, result=result, errors=errors_list)


class EditAccountInput(graphene.InputObjectType):
    email = graphene.String()
    name = graphene.String()
    surnames = graphene.String()
    phone_number = graphene.String()
    is_vip = graphene.Boolean()
    is_active = graphene.Boolean()
    is_staff = graphene.Boolean()


class EditAccount(graphene.Mutation):
    email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        input = graphene.Argument(EditAccountInput)

    def mutate(self, info, input):
        result = settings.KO
        errors_list = []

        email = input.email
        name = input.name
        surnames = input.surnames
        phone_number = input.phone_number

        email_pattern = re.compile(settings.EMAIL_REGEX_PATTERN)
        if email is None or len(email.strip()) == 0:
            errors_list.append(settings.EMAIL_REQUIRED_ERROR)
        elif email_pattern.match(email) is None:
            errors_list.append(settings.EMAIL_REGEX_ERROR)

        if name is None or len(name.strip()) == 0:
            errors_list.append(settings.NAME_REQUIRED_ERROR)

        if surnames is None or len(surnames.strip()) == 0:
            errors_list.append(settings.SURNAMES_REQUIRED_ERROR)

        if phone_number is None or len(phone_number.strip()) == 0:
            errors_list.append(settings.PHONE_NUMBER_REQUIRED_ERROR)
        else:
            try:
                parsed_phone_number = phonenumbers.parse(phone_number)
                if not phonenumbers.is_valid_number(parsed_phone_number):
                    errors_list.append(settings.PHONE_NUMBER_NOT_VALID_ERROR)
            except phonenumbers.NumberParseException:
                errors_list.append(settings.PHONE_NUMBER_NOT_VALID_ERROR)

        edited_user = None  # account to edit
        logged_in_user = info.context.user
        if logged_in_user.is_anonymous:
            errors_list.append(settings.USER_NOT_LOGGED_IN_ERROR)
        elif not logged_in_user.is_active:
            errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)
        elif logged_in_user.email == email:
            # when an user is editing own account
            edited_user = logged_in_user
        elif logged_in_user.is_staff:
            # when a staff user is editing another account
            try:
                edited_user = get_user_model().objects.get(email=email.lower())
            except get_user_model().DoesNotExist:
                errors_list.append(settings.ACCOUNT_DOES_NOT_EXIST_ERROR)
        else:
            errors_list.append(settings.OPERATION_NOT_ALLOWED_ERROR)

        if len(errors_list) == 0:
            edited_user.first_name = input.name
            edited_user.last_name = input.surnames
            edited_user.phone_number = input.phone_number
            if logged_in_user.is_staff:
                # This changes can only be done by a staff account
                edited_user.is_vip = input.is_vip
                edited_user.is_active = input.is_active
                edited_user.is_staff = input.is_staff

            edited_user.save()

            result = settings.OK

        return EditAccount(email=input.email, result=result, errors=errors_list)


class ActivateAccount(graphene.Mutation):
    email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        token = graphene.String()

    def mutate(self, info, token):
        email = None
        # result = settings.USER_NOT_ACTIVATED_ERROR
        result = settings.KO
        errors_list = []

        if token is None or len(token.strip()) == 0:
            errors_list.append(settings.TOKEN_REQUIRED_ERROR)
        else:
            try:
                payload = jwt_decode(token)
                email = payload.get('email')

                if email is None or len(email.strip()) == 0:
                    raise Exception()

                user = None
                try:
                    user = get_user_model().objects.get(email=email.lower())
                except get_user_model().DoesNotExist:
                    errors_list.append(settings.ACCOUNT_DOES_NOT_EXIST_ERROR)

                if user is not None:
                    if user.is_active:
                        errors_list.append(settings.ACCOUNT_ACTIVE_ERROR)
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

        return ActivateAccount(email=email, result=result, errors=errors_list)


class DeactivateAccount(graphene.Mutation):
    email = graphene.String()
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
            errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)

        if len(errors_list) == 0:
            user.is_active = False
            user.is_used_last_token = True
            user.save()
            # result = settings.USER_DEACTIVATED
            result = settings.OK

        return DeactivateAccount(email=user.email, result=result, errors=errors_list)


class UpdateEmail(graphene.Mutation):
    old_email = graphene.String()
    new_email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        token = graphene.String()

    def mutate(self, info, token):
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
                old_email = payload.get('email')
                new_email = payload.get('new_email')

                email_pattern = re.compile(settings.EMAIL_REGEX_PATTERN)
                if old_email is None or len(old_email.strip()) == 0 \
                        or new_email is None or len(new_email.strip()) == 0 is None:
                    raise Exception()
                elif email_pattern.match(new_email) is None:
                    errors_list.append(settings.EMAIL_REGEX_ERROR)
                elif get_user_model().objects.filter(email__iexact=new_email).exists():
                    errors_list.append(settings.EMAIL_ALREADY_REGISTERED_ERROR)
                else:
                    user = None
                    try:
                        user = get_user_model().objects.get(email=old_email)
                    except get_user_model().DoesNotExist:
                        errors_list.append(settings.ACCOUNT_DOES_NOT_EXIST_ERROR)

                    if user is not None:
                        if not user.is_active:
                            errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)
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

        return UpdateEmail(old_email=old_email, new_email=new_email, result=result, errors=errors_list)


class ChangePassword(graphene.Mutation):
    email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        password1 = graphene.String()
        password2 = graphene.String()

    def mutate(self, info, password1, password2):
        email = None
        result = settings.KO
        errors_list = []

        user = info.context.user
        if user.is_anonymous:
            errors_list.append(settings.USER_NOT_LOGGED_IN_ERROR)
        elif not user.is_active:
            errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)

        if password1 is None or len(password1.strip()) == 0:
            errors_list.append(settings.PASSWORD1_REQUIRED_ERROR)

        if password2 is None or len(password2.strip()) == 0:
            errors_list.append(settings.PASSWORD2_REQUIRED_ERROR)

        if password1 != password2:
            errors_list.append(settings.PASSWORDS_NOT_MATCH_ERROR)
        else:
            password_pattern = re.compile(settings.PASSWORD_REGEX_PATTERN)
            if password_pattern.match(password1) is None:
                errors_list.append(settings.PASSWORD_REGEX_ERROR)

        if len(errors_list) == 0:
            user.set_password(password1)
            user.save()

            result = settings.OK

        return ChangePassword(email=email, result=result, errors=errors_list)


class ResetPassword(graphene.Mutation):
    email = graphene.String()
    result = graphene.String()
    errors = graphene.List(graphene.String)

    class Arguments:
        token = graphene.String()
        password1 = graphene.String()
        password2 = graphene.String()

    def mutate(self, info, token, password1, password2):
        email = None
        # result = settings.PASSWORD_NOT_RESET_ERROR
        result = settings.KO
        errors_list = []

        if password1 is None or len(password1.strip()) == 0:
            errors_list.append(settings.PASSWORD1_REQUIRED_ERROR)

        if password2 is None or len(password2.strip()) == 0:
            errors_list.append(settings.PASSWORD2_REQUIRED_ERROR)

        if password1 != password2:
            errors_list.append(settings.PASSWORDS_NOT_MATCH_ERROR)
        else:
            password_pattern = re.compile(settings.PASSWORD_REGEX_PATTERN)
            if password_pattern.match(password1) is None:
                errors_list.append(settings.PASSWORD_REGEX_ERROR)

        if token is None or len(token.strip()) == 0:
            errors_list.append(settings.TOKEN_REQUIRED_ERROR)
        else:
            try:
                payload = jwt_decode(token)
                email = payload.get('email')
                if email is None or len(email.strip()) == 0:
                    raise Exception()

                user = None
                try:
                    user = get_user_model().objects.get(email=email)
                except get_user_model().DoesNotExist:
                    errors_list.append(settings.ACCOUNT_DOES_NOT_EXIST_ERROR)

                if user is not None:
                    if not user.is_active:
                        errors_list.append(settings.ACCOUNT_INACTIVE_ERROR)
                    elif token != user.last_token:
                        errors_list.append(settings.TOKEN_NOT_MATCH_ERROR)
                    elif user.is_used_last_token:
                        errors_list.append(settings.TOKEN_USED_ERROR)

                    if len(errors_list) == 0:
                        # https://django-graphql-jwt.domake.io/en/stable/settings.html#pyjwt
                        user.set_password(password1)
                        user.is_used_last_token = True
                        user.save()

                        # result = settings.PASSWORD_RESET
                        result = settings.OK

            except ExpiredSignatureError:
                errors_list.append(settings.EXPIRED_TOKEN_ERROR)
            except Exception:
                errors_list.append(settings.TOKEN_ERROR)

        return ResetPassword(email=email, result=result, errors=errors_list)


class Mutation(graphene.ObjectType):
    send_verification_email = SendVerificationEmail.Field()
    create_account = CreateAccount.Field()
    edit_account = EditAccount.Field()
    activate_account = ActivateAccount.Field()
    deactivate_account = DeactivateAccount.Field()
    update_email = UpdateEmail.Field()
    change_password = ChangePassword.Field()
    reset_password = ResetPassword.Field()
