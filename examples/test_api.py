import asyncio

from pssapi import PssApiClient


async def main():
    client = PssApiClient()

    setting = await client.get_latest_version()

    print("Respuesta recibida:")
    print(setting)

    print()
    print("Servidor de producción:")
    print(setting.production_server)


if __name__ == "__main__":
    asyncio.run(main())
