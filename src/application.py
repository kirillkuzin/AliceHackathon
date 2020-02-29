import subprocess
from aiohttp import web

from aioalice import Dispatcher, get_new_configured_app
from aioalice.dispatcher import MemoryStorage

from states import UserStates, DosStates, PingStates
import meta
import utils


WEBHOOK_URL_PATH = '/my-alice-webhook/'

WEBAPP_PORT = 8080

SKOLTECH_URL = 'cb.skoltech.ru'


dp = Dispatcher(storage=MemoryStorage())


@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.set_state(user_id, UserStates.INPUT_SERVER)
    return alice_request.response('Привет! Напиши мне свой сервер')


@dp.request_handler(state=UserStates.INPUT_SERVER)
async def handle_input_server(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    await dp.storage.update_data(user_id=user_id,
                                 data={'server': SKOLTECH_URL})
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    return alice_request.response('Я запомнила. Теперь выбери что будем '
                                  'делать. Я могу выполнить пинг, '
                                  'запустить Dos атаку, просканировать порты '
                                  'и сайт на уязвимость',
                                  buttons=meta.action_buttons)


@dp.request_handler(state=UserStates.SELECT_COMMAND,
                    contains=['атаковать', 'атака', 'атакуй',
                              'ddos', 'dos', 'дудос', 'ддос', 'дидос'])
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
    addr = request_text
    if 'мой сервер' in request_text:
        data = await dp.storage.get_data(user_id)
        server = data['server']
        addr = server
    result = utils.ping(addr)
    if result == 0:
        proc = subprocess.Popen(
            ['python', './src/test_http.py', addr]
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
    data['dos'].terminate()
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    return alice_request.response('Сервер будет жить. Что дальше ?',
                                  buttons=meta.action_buttons)


@dp.request_handler(state=DosStates.START_ATTACK)
async def handle_try_stop_attack(alice_request):
    return alice_request.response('У тебя никогда не получится меня '
                                  'остановить')


@dp.request_handler(state=UserStates.SELECT_COMMAND,
                    contains=['пинг', 'ping', 'pink',
                              'доступен', 'доступность'])
async def handle_select_host_ping(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.set_state(user_id, PingStates.SELECT_HOST_PING)
    return alice_request.response('Какой хост пингуем ?')


@dp.request_handler(state=PingStates.SELECT_HOST_PING)
async def handle_start_ping(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    addr = request_text
    if 'мой сервер' in request_text:
        data = await dp.storage.get_data(user_id)
        server = data['server']
        addr = server
    result = utils.ping(addr)
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
