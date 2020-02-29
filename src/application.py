import subprocess
from aiohttp import web

from aioalice import Dispatcher, get_new_configured_app
from aioalice.dispatcher import MemoryStorage

from states import UserStates, DosStates, PingStates
import meta
import utils


WEBHOOK_URL_PATH = '/my-alice-webhook/'

WEBAPP_PORT = 8080


dp = Dispatcher(storage=MemoryStorage())


@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    return alice_request.response('Привет! Что будем делать ?',
                                  buttons=meta.action_buttons)


@dp.request_handler(state=UserStates.SELECT_COMMAND,
                    contains=['атаковать', 'атака'])
async def handle_select_host_attack(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.update_data(user_id=user_id,
                                 data={'dos': None})
    await dp.storage.set_state(user_id, DosStates.SELECT_HOST_DOS)
    return alice_request.response('Какой хост атакуем ?')


@dp.request_handler(state=DosStates.SELECT_HOST_DOS)
async def handle_start_attack(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    print(request_text)
    result = utils.ping(request_text)
    if result == 0:
        addr = request_text
        if request_text == 'мой сервер':
            addr = 'cb.skoltech.ru'
        proc = subprocess.Popen(
            ['python', './src/test_http.py', request_text]
        )
        await dp.storage.update_data(user_id=user_id,
                                     data={'dos': proc})
        await dp.storage.set_state(user_id, DosStates.START_ATTACK)
        print(proc.pid)
        return alice_request.response('Атака на Сколтех началась')
    else:
        await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
        return alice_request.response('Невалидный хост')


@dp.request_handler(state=DosStates.START_ATTACK,
                    commands=['стоп', 'хватит', 'прекрати',
                              'остановись', 'нельзя', 'фу',
                              'отмена'])
async def handle_stop_attack(alice_request):
    user_id = alice_request.session.user_id
    data = await dp.storage.get_data(user_id)
    proc = data['dos']
    proc.terminate()
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    return alice_request.response('Остановочка. Что дальше ?',
                                  buttons=meta.action_buttons)


@dp.request_handler(state=UserStates.SELECT_COMMAND,
                    contains=['пинг', 'ping', 'pink'])
async def handle_select_host_ping(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.set_state(user_id, PingStates.SELECT_HOST_PING)
    return alice_request.response('Какой хост пингуем ?')


@dp.request_handler(state=PingStates.SELECT_HOST_PING)
async def handle_start_ping(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    result = utils.ping(request_text)
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    if result == 0:
        return alice_request.response('Пакетики доставлены. Что дальше ?',
                                      buttons=meta.action_buttons)
    else:
        return alice_request.response('Пакетики не доставлены. Что дальше ?',
                                      buttons=meta.action_buttons)


@dp.request_handler(state=UserStates.SELECT_COMMAND)
async def handle_other_commands(alice_request):
    return alice_request.response('Читай доки',
                                  buttons=meta.action_buttons)


if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host='0.0.0.0', port=WEBAPP_PORT)
