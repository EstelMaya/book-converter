from methods import convert_docx, convert_epub, convert_pdf
from os import getuid, getenv
from aiohttp import web
import asyncio
from connexion import AioHttpApp
from io import BytesIO

MAX_SIZE = int(getenv('MAX_BOOK_SIZE_BYTES', 8192**2))


async def handle_health(request):
    # healthcheck method, required for kubernetes
    return web.Response(content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})

async def handle_whoami(request):
    text = "AMAI file converter ver. 0.0.5\nImplemented by: k@amai.io\nAdapted by: p.dondukov@amai.io"
    return web.Response(text=text, content_type='text/plain', headers={'Access-Control-Allow-Origin': '*'})


async def handle_convert(request, file_type=None):
    fs = BytesIO(await request.read())
    loop  = asyncio.get_running_loop()

    
    match file_type:
        case "pdf":
            func = convert_pdf
        case "epub":
            func = convert_epub
        case "docx":
            func = convert_docx
        case _:
            err_text = f"Can't convert file to json. File type \"{file_type}\" is not supported."
            print(err_text)
            return web.Response(status=400, text=err_text, content_type='text/plain', headers={'Access-Control-Allow-Origin': '*'})

    output = await loop.run_in_executor(None, func, fs)
    return web.json_response(output, status=200, headers={'Access-Control-Allow-Origin': '*'})


if __name__ == '__main__':
    port = 80 if getuid() == 0 else 8080

    app = AioHttpApp(__name__, port=port, server_args={"client_max_size": MAX_SIZE})
    app.add_api('openapi.yaml', pass_context_arg_name='request')
    app.run()
