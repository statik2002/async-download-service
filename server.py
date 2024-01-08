import asyncio
import os.path
from datetime import datetime
from subprocess import Popen, PIPE

import aiohttp.web
from aiohttp import web
import aiofiles

INTERVAL_SECS = 1


async def archive(request):
    hash = request.match_info.get('archive_hash', 'hz')
    args_set = ['-r', '-', '.']

    if not os.path.exists(f'test_photos/{hash}/'):
        async with aiofiles.open('404.html', mode='r') as error_file:
            error_contents = await error_file.read()
        raise aiohttp.web.HTTPNotFound(body=error_contents, content_type='text/html')

    proc = await asyncio.create_subprocess_exec(
        'zip', *args_set, stdout=PIPE, stderr=PIPE, cwd=f'test_photos/{hash}/')
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
    ])
    web.run_app(app)
