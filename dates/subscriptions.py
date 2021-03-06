from .models import Appointment, AppointmentState
from graphene import relay
from graphene_django import DjangoObjectType

import channels_graphql_ws
import graphene


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
    CREATE_APPOINTMENT_STATE = "Create_appointment"
    UPDATE_APPOINTMENT_STATE = "Update_appointment"
    DELETE_APPOINTMENT_STATE = "Delete_appointment"


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
