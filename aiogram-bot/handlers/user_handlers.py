from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states import Registration
from services.validator import is_valid_phone
from database.models import db_manager

router = Router()

# Исправленная строка:
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Давай зарегистрируемся. Введите своё имя.")
    await state.set_state(Registration.name)

@router.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Теперь введи номер телефона (РФ, например, +79991234567):")
    await state.set_state(Registration.phone)

@router.message(Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if not is_valid_phone(message.text):
        await message.answer("Неверный формат номера. Попробуй еще раз (+7.. или 8..):")
        return
    await state.update_data(phone=message.text)
    await message.answer("Какое твое хобби?")
    await state.set_state(Registration.activity)

@router.message(Registration.activity)
async def process_activity(message: types.Message, state: FSMContext):
    data = await state.update_data(activity=message.text)
    
    await db_manager.save_user(message.from_user.id, data['name'], data['phone'], data['activity'])
    
    await message.answer(f"Спасибо, {data['name']}! Теперь мы можем обсудить {data['activity']}.")
    await state.clear()
