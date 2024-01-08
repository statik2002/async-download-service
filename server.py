import asyncio
from datetime import datetime
from subprocess import Popen, PIPE
from aiohttp import web
import aiofiles

INTERVAL_SECS = 1


class Handler:

    def __init__(self):
        pass

    async def handle_archive(self, request):
        hash = request.match_info.get('archive', 'hz')

        return web.Response()


async def uptime_handler(request):
    response = web.StreamResponse()

    # Большинство браузеров не отрисовывают частично загруженный контент, только если это не HTML.
    # Поэтому отправляем клиенту именно HTML, указываем это в Content-Type.
    response.headers['Content-Type'] = 'text/html'

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)

    while True:
        formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f'{formatted_date}<br>'  # <br> — HTML тег переноса строки

        # Отправляет клиенту очередную порцию ответа
        await response.write(message.encode('utf-8'))

        await asyncio.sleep(INTERVAL_SECS)


async def archive(request):
    hash = request.match_info.get('archive_hash', 'hz')
    args_set = ['-r', '-', '.']
    proc = await asyncio.create_subprocess_exec('zip', *args_set, stdout=PIPE, stderr=PIPE, cwd=f'test_photos/{hash}/')
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="archive.zip"'
    await response.prepare(request)

    with open('photos.zip', 'wb') as f:
        while True:
            stdout = await proc.stdout.read(100 * 1024)
            if not stdout:
                break

            await response.write(stdout)

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
        web.get('/time/', uptime_handler)
    ])
    web.run_app(app)
