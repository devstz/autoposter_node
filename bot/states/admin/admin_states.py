from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    SEND_MSG_FOR_POST = State()

    EDIT_PRICE = State()

    SET_MESSAGE_CHANNEL = State()

    # Groups binding flow
    SEND_GROUP_IDS = State()

    # Distribution creation flow
    DISTRIBUTION_WAIT_NAME = State()
    DISTRIBUTION_WAIT_MODE = State()
    DISTRIBUTION_WAIT_GROUP_IDS = State()
    DISTRIBUTION_SELECT_BOTS = State()
    DISTRIBUTION_WAIT_PAUSE = State()
    DISTRIBUTION_WAIT_DELETE_LAST = State()
    DISTRIBUTION_WAIT_PIN = State()
    DISTRIBUTION_WAIT_PIN_FREQUENCY = State()
    DISTRIBUTION_WAIT_TARGET_ATTEMPTS = State()
    DISTRIBUTION_WAIT_SOURCE = State()
