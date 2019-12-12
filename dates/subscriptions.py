import channels_graphql_ws
import graphene

from .models import Appointment, AppointmentState, UserInfo
from graphene import relay
from graphene_django import DjangoObjectType


# Nodes moved from schema.py to subscriptions.py to avoid import problems
class UserInfoNode(DjangoObjectType):
    class Meta:
        model = UserInfo
        exclude_fields = ('last_token', 'is_used_last_token', 'created', 'edited')

        # Filter fields for relay queries
        filter_fields = {
            'user': ['exact'],
            'user__username': ['exact', 'contains', 'istartswith'],
            'user__first_name': ['exact', 'contains', 'istartswith'],
            'user__last_name': ['exact', 'contains', 'istartswith'],
            'user__email': ['exact', 'contains'],
        }

        # Necessary for relay
        interfaces = (relay.Node,)


class AppointmentStateNode(DjangoObjectType):
    class Meta:
        model = AppointmentState
        exclude_fields = ('created', 'edited')
        filter_fields = [
            'name',
            'appointments']
        interfaces = (relay.Node,)


class AppointmentNode(DjangoObjectType):
    class Meta:
        model = Appointment
        exclude_fields = ('created', 'edited')
        filter_fields = [
            'user',
            'appointment_date',
            'appointment_state'
        ]
        interfaces = (relay.Node,)


class AppointmentStateActionEnum(graphene.Enum):
    CREATE_APPOINTMENT_STATE = "Create"
    UPDATE_APPOINTMENT_STATE = "Update"
    DELETE_APPOINTMENT_STATE = "Delete"


class OnAppointmentState(channels_graphql_ws.Subscription):
    """Subscription triggers on a new appointment state."""

    action = graphene.String()
    appointment_state_node = graphene.Field(AppointmentStateNode)

    class Arguments:
        """Subscription arguments."""
        action = graphene.Argument(AppointmentStateActionEnum, required=True)

    def subscribe(self, info, action=None):
        """Client subscription handler."""
        del info
        # Specify the subscription group client subscribes to.
        return ["appointment_state_{}".format(action)]

    def publish(self, info, action=None):
        """Called to prepare the subscription notification appointment state."""
        del info

        # The `self` contains payload delivered from the `broadcast()`.
        action = self["action"]
        appointment_state_node = self["appointment_state_node"]

        return OnAppointmentState(action=action, appointment_state_node=appointment_state_node)

    @classmethod
    def action_appointment_state(cls, action, appointment_state_node):
        """Auxiliary function to send subscription notifications.
        It is generally a good idea to encapsulate broadcast invocation
        inside auxiliary class methods inside the subscription class.
        That allows to consider a structure of the `payload` as an
        implementation details.
        """
        cls.broadcast(
            group="appointment_state_{}".format(action),
            payload={"action": action, "appointment_state_node": appointment_state_node})
