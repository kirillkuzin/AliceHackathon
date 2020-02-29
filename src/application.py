from aiohttp import web

from aioalice import Dispatcher, get_new_configured_app
from aioalice.dispatcher import MemoryStorage


WEBHOOK_URL_PATH = '/my-alice-webhook/'

WEBAPP_PORT = 5000


dp = Dispatcher(storage=MemoryStorage())


@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    # user_id = alice_request.session.user_id
    return alice_request.response('Привет! Какой хост атакуем ?')


@dp.request_handler()
async def handle_all_other_requests(alice_request):
    pass


if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host='127.0.0.1', port=WEBAPP_PORT)
