import asyncio
import logging
from contextlib import asynccontextmanager

import asyncpg

logger = logging.getLogger("asyncpg")

class AsyncPGClient:

    '''
    Асинхронный клиент для работы с PostgreSQL через asyncpg
    '''

    def __init__(self,
                 dsn: str,
                 min_size: int = 10,
                 max_size: int = 30,
                 max_queries: int = 50000,
                 connection_timeout: float = 300.0,
                 **kwargs) -> None:
        '''
        Инициализация клиента

        :param dsn: Data Source Name для подключения к базе данных. Пример: postgresql://user:password@localhost:5432/db_name
        '''

        self._dsn = dsn
        self._pool: asyncpg.Pool = None
        self._pool_params = {
            "min_size": min_size,
            "max_size": max_size,
            "max_queries": max_queries,
            "max_inactive_connection_lifetime": connection_timeout,
            **kwargs
        }
        logger.debug("AsyncPG is ready")
    
    async def connect(self) -> None:
        '''
        Создание пула соединений с базой данных
        '''

        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    dsn=self._dsn,
                    **self._pool_params
                )
                logger.info(f"Pool created with min={self._pool_params['min_size']}, "
                          f"max={self._pool_params['max_size']} connections")
            except Exception as ex:
                logger.error(f"Failed to create the connection pool", exc_info=True)
                raise
    
    async def disconnect(self) -> None:
        '''
        Закрытие пула соединений.
        '''

        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Connection pool was closed")

    @asynccontextmanager
    async def get_connection(self):
        '''
        Контекстный менеджер для получения соединения из пула.
        
        Пример использования:
            async with client.get_connection() as conn:
                await conn.execute(...)
        '''

        if self._pool is None:
            await self.connect()
        
        async with self._pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        '''
        Выполнение SQL команды с возвратом статуса
        
        :param query: SQL запрос
        :type query: str
        '''
        conn: asyncpg.Connection
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(query, *args)
                logger.debug(f'EXECUTE: {query} == {result}')
                return result
        except Exception as e:
            logger.error(f"Error executing query: {query}", exc_info=True)
            raise
    
    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        '''
        Выполнение запроса с возвратом записей
        
        :param query: SQL запрос
        :type query: str
        '''
        conn: asyncpg.Connection
        try:
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *args)
                logger.debug(f'FETCH: {query} == {result}')
                return result
        except Exception as e:
            logger.error(f"Error executing query: {query}", exc_info=True)
            raise
    
    async def fetchrow(self, query: str, *args) -> asyncpg.Record:
        '''
        Выполнение запроса для одной строки с возвратом значений/записи
        
        :param query: SQL запрос
        :type query: str
        '''
        conn: asyncpg.Connection
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                logger.debug(f'FETCHROW: {query} == {result}')
                return result
        except Exception as e:
            logger.error(f"Error executing query: {query}", exc_info=True)
            raise
    
    async def fetchval(self, query: str, *args):
        '''
        Выполнение запроса для одной строки с возвратом значения
        
        :param query: SQL запрос
        :type query: str
        '''
        conn: asyncpg.Connection
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval(query, *args)
                logger.debug(f'FETCHVAL: {query} == {result}')
                return result
        except Exception as e:
            logger.error(f"Error executing query: {query}", exc_info=True)
            raise