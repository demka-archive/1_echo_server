import socket
import logging
import random
from server_validator import port_validation, check_port_open
import yaml
import json
from typing import Dict
from data_processing import DataProcessing

END_MESSAGE_FLAG = "CRLF"
DEFAULT_PORT = 9090

# Настройки логирования
logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
    handlers=[logging.FileHandler("./logs/server.log"), logging.StreamHandler()],
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Server:
    def __init__(self, port_number: int) -> None:

        logging.info(f"Запуск сервера..")

        self.database = DataProcessing()

        sock = socket.socket()
        sock.bind(("", port_number))
        sock.listen(0)
        # Наш сокет
        self.sock = sock
        # Список авторизации
        self.authenticated_list = []
        logging.info(f"Сервер инициализировался, слушает порт {port_number}")
        # Ожидаем новое подключение

        while True:
            # Новое соединение
            conn, addr = self.sock.accept()
            logging.info(f"Новое соединение от {addr[0]}")
            self.client_router(conn, addr)

    def message_logic(self, conn, client_ip):
        """
        Получение сообщений
        """
        data = ""
        while True:
            # Получаем данные и собираем их по кусочкам
            chunk = conn.recv(1024)
            data += chunk.decode()

            # Если это конец сообщения, то значит, что мы все собрали и можем обратно отдавать клиенту
            if END_MESSAGE_FLAG in data:

                logging.info(f"Получили сообщение {data} от клиента {client_ip}")

                conn.send(data.encode())
                logging.info(
                    f"Сообщение {data} было отправлено обратно клиенту {client_ip}"
                )
                data = ""

            # Значит пришла только часть большого сообщения
            else:
                logger.info(f"Приняли часть данных от клиента {client_ip}: '{data}'")

            # Если вообще ничего не пришло - это конец всего соединения
            if not chunk:
                break

    def auth_logic(self, conn, addr):
        """
        Логика авторизации клиента

        Запрос авторизации у нас априори меньше 1024, так что никакой цикл не запускаем
        """
        user_password = json.loads(conn.recv(1024).decode())["password"]
        client_ip = addr[0]

        # Проверяем на существование данных
        auth_result, username = self.database.user_auth(client_ip, user_password)

        # Если авторизация прошла успешно
        if auth_result:
            logger.info(f"Клиент {client_ip} -> авторизация прошла успешно")
            data = json.dumps(
                {"result": True, "body": {"username": username}}, ensure_ascii=False
            )
            self.authenticated_list.append(client_ip)
            logging.info(f"Добавили клиента {client_ip} в список авторизации")

        # Если авторизация не удалась
        else:
            logger.info(f"Клиент {client_ip} -> авторизация не удалась")
            data = json.dumps({"result": False}, ensure_ascii=False)

        conn.send(data.encode())
        logger.info(f"Клиент {client_ip}. Отправили данные о результате авторизации")

        # Если была авторизация - принимаем последующие сообщения от пользователя
        if auth_result:
            self.message_logic(conn, client_ip)

    # def login_logic
    def client_router(self, conn, addr):
        """
        Роутинг пользователя в зависимости от его авторизации
        """
        client_ip = addr[0]

        # Если ip не авторизован - надо авторизовать
        # if client_ip not in self.authenticated_list:
        if client_ip not in self.authenticated_list:
            self.auth_logic(conn, addr)

        # Если уже был авторизован
        else:
            self.message_logic(conn, client_ip)

        logging.info(f"Отключение клиента {client_ip}")

        # Если клиент был в списке авторизации - удаляем его
        if client_ip in self.authenticated_list:
            self.authenticated_list.remove(client_ip)
            logging.info(f"Удалили клиента {client_ip} из списка авторизации")

    def __del__(self):
        logging.info(f"Остановка сервера")


def main():

    port_input = input("Введите номер порта для сервера -> ")
    # Тут проверка на то, занят ли порт
    port_flag = port_validation(port_input, check_open=True)

    if not port_flag:

        # Если порт по-умолчанию уже занят, то перебираем свободные порты
        if not check_port_open(DEFAULT_PORT):
            print(
                f"Порт по умолчанию {DEFAULT_PORT} уже занят! Подбираем рандомный порт.."
            )
            stop_flag = False
            while not stop_flag:
                current_port = random.randint(49152, 65535)
                print(f"Сгенерировали рандомный порт {current_port}")
                stop_flag = check_port_open(current_port)

            port_input = current_port
        else:
            port_input = DEFAULT_PORT
        print(f"Выставили порт {port_input} по умолчанию")

    server = Server(int(port_input))


if __name__ == "__main__":
    main()
