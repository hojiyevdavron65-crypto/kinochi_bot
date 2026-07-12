from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    waiting_for_file = State()
    waiting_for_code = State()
    waiting_for_title = State()


class DeleteMovie(StatesGroup):
    waiting_for_code = State()


class Broadcast(StatesGroup):
    waiting_for_message = State()