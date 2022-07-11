import aiohttp
import asyncio
from argparse import ArgumentParser
from json import dump, loads
from os.path import splitext

parser = ArgumentParser()
parser.add_argument("-b", "--book")
parser.add_argument("-u", "--url", default="http://localhost")
parser.add_argument("-p", "--port")
args = parser.parse_args()

format = splitext(args.book)[1][1:]
port = ":"+args.port if args.port else ""


async def main():
    with open(args.book, 'rb') as f:
        msg = f.read()
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{args.url}{port}/api/v1/convert/{format}', data=msg) as r:
            out = await r.read()
            data = loads(out.decode())
    with open('output.json', 'w') as f:
        dump(data, f, ensure_ascii=False)

asyncio.run(main())
