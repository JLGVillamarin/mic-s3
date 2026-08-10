from amiga.servers.rest import AmigaServer, RestService


def main():
    server = AmigaServer()
    server.add_service(RestService(["mic_s3.controllers"]))
    server.launch()


if __name__ == "__main__":
    main()
