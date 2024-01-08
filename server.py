import asyncio
import os.path
from subprocess import PIPE
import logging
import aiohttp.web
from aiohttp import web
import aiofiles

INTERVAL_SECS = 1

logging.basicConfig(level=logging.DEBUG)


async def archive(request):
    dir_hash = request.match_info.get('archive_hash', 'hz')
    args_set = ['-r', '-', '.']

    if not os.path.exists(f'test_photos/{dir_hash}/'):
        async with aiofiles.open('404.html', mode='r') as error_file:
            error_contents = await error_file.read()
        raise aiohttp.web.HTTPNotFound(body=error_contents, content_type='text/html')

    proc = await asyncio.create_subprocess_exec(
        'zip', *args_set, stdout=PIPE, stderr=PIPE, cwd=f'test_photos/{dir_hash}/')
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="archive.zip"'
    await response.prepare(request)

    try:
        while True:
            logging.info(u'Sending archive chunk ...')
            stdout = await proc.stdout.read(100 * 1024)
            if not stdout:
                break

            await response.write(stdout)
            await asyncio.sleep(10)

        return response

    except asyncio.CancelledError:
        proc.kill()
        logging.info(u'Download was interrupted')

        raise

    except IndexError:
        proc.kill()
        logging.info(u'Too big')
        raise

    except SystemExit:
        proc.kill()
        logging.info(u'SystemExit')
        raise

    except KeyboardInterrupt:
        proc.kill()
        logging.info(u'Keyboard Interrupted')
        raise

    finally:
        proc.kill()
        return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(
        format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
        level=logging.DEBUG
    )
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
