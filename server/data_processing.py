import yaml
from typing import Dict, Tuple, Union


class DataProcessing:
    """Класс для работы с коллекцией пользователей в yaml"""

    def __init__(self) -> None:
        self.file_path = "./data/users.yml"
        self.data = []
        self.read_collection()

    def read_collection(self):
        """Чтение данных с файла в self.data"""
        with open(self.file_path, "r") as stream:
            self.data = yaml.safe_load(stream)

    def write_collection(self):
        """Запись данных с self.data в файл"""
        with open(self.file_path, "r") as stream:
            yaml.dump(self.data, stream)

    def user_auth(self, ip: str, password: str) -> Tuple[bool, Union[str, None]]:
        """Метод авторизации пользователя в системе"""
        for user in self.data:
            if user["ip_addr"] == ip and user["password"] == password:
                return True, user["username"]
        return False, None

    def user_reg(self, ip: str, password: str, username: str) -> None:
        """Метод регистрации пользователей"""
        self.data.append({"ip": ip, "password": password, "username": username})
        self.write_collection()
