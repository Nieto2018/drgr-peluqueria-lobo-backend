from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql_relay.node.node import from_global_id

from .subscriptions import \
    AppointmentNode, \
    AppointmentStateActionEnum, \
    AppointmentStateNode, \
    AppointmentState, \
    OnAppointmentState, \
    UserInfoNode

import graphene


class CreateAppointmentState(graphene.Mutation):
    # Relay allows Output objects
    appointment_state_node = graphene.Field(AppointmentStateNode)

    # Important!!! Relay not allows Input objects as arguments
    class Arguments:
        name = graphene.String(required=True)

    def mutate(self, info, name):
        appointment_state = AppointmentState(name=name)
        appointment_state.save()

        OnAppointmentState.action_appointment_state(
            action=AppointmentStateActionEnum.CREATE_APPOINTMENT_STATE.value,
            appointment_state_node=appointment_state
        )

        return CreateAppointmentState(appointment_state_node=appointment_state)


class UpdateAppointmentState(graphene.Mutation):
    appointment_state_node = graphene.Field(AppointmentStateNode)

    class Arguments:
        id = graphene.String(required=True)
        name = graphene.String(required=True)

    def mutate(self, info, id, name):
        # Ged integer ID from String Graphql global ID
        int_id = int(from_global_id(id)[1])

        appointment_state = AppointmentState.objects.get(pk=int_id)
        appointment_state.name = name
        appointment_state.save()

        OnAppointmentState.action_appointment_state(
            action=AppointmentStateActionEnum.UPDATE_APPOINTMENT_STATE.value,
            appointment_state_node=appointment_state
        )

        return UpdateAppointmentState(appointment_state_node=appointment_state)


class DeleteAppointmentState(graphene.Mutation):
    appointment_state_node = graphene.Field(AppointmentStateNode)

    class Arguments:
        id = graphene.String(required=True)

    def mutate(self, info, id):
        # Ged integer ID from String Graphql global ID
        int_id = int(from_global_id(id)[1])

        appointment_state = AppointmentState.objects.get(pk=int_id)
        appointment_state.delete()

        OnAppointmentState.action_appointment_state(
            action=AppointmentStateActionEnum.DELETE_APPOINTMENT_STATE.value,
            appointment_state_node=appointment_state
        )

        return DeleteAppointmentState(appointment_state_node=appointment_state)


class Query(graphene.ObjectType):
    """Root GraphQL query."""

    relay_user_info = relay.Node.Field(UserInfoNode)
    relay_user_infos = DjangoFilterConnectionField(UserInfoNode)

    relay_appointment_state = relay.Node.Field(AppointmentStateNode)
    relay_appointment_states = DjangoFilterConnectionField(AppointmentStateNode)

    relay_appointment = relay.Node.Field(AppointmentNode)
    relay_appointments = DjangoFilterConnectionField(AppointmentNode)


class Mutation(graphene.ObjectType):
    """GraphQL mutations."""

    create_appointment_state = CreateAppointmentState.Field()
    update_appointment_state = UpdateAppointmentState.Field()
    delete_appointment_state = DeleteAppointmentState.Field()


class Subscription(graphene.ObjectType):
    """GraphQL """

    on_appointment_state_action = OnAppointmentState.Field()
