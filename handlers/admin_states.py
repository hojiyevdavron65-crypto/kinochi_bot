from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    waiting_for_file = State()
    waiting_for_code = State()
    waiting_for_caption = State()


class AddEpisode(StatesGroup):
    """Mavjud kodga yangi qism qo'shish uchun."""
    waiting_for_code = State()
    waiting_for_episode_number = State()
    waiting_for_file = State()
    waiting_for_caption = State()


class DeleteMovie(StatesGroup):
    waiting_for_code = State()


class Broadcast(StatesGroup):
    waiting_for_message = State()