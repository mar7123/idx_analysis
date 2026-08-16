from typing import Mapping
from sqlalchemy import Engine, Connection, create_engine, text
from idxanalysis.utils.LogUtils import LogUtils


class __DbConfig:
    __USER = "root"
    __PASSWORD = "password"
    __HOST = "localhost"
    __DATABASE = "idx"
    __engine: Engine | None = None

    def __get_engine(self) -> Engine:
        if self.__engine is None:
            self.__engine = create_engine(
                f"mysql+pymysql://{self.__USER}:{self.__PASSWORD}@{self.__HOST}/{self.__DATABASE}"
            )
        return self.__engine

    def create_db_connection(self) -> Connection:
        return self.__get_engine().connect()

    def query(self, connection: Connection, sql: str, parameters: list[Mapping[str, object]] | Mapping[str, object] | None = None):
        result = connection.execute(text(sql), parameters=parameters)
        LogUtils.append_log(f"Query\n{sql}\nRow Count {result.rowcount}")
        return result


dbConfig = __DbConfig()
