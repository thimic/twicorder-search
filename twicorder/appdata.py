#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiosqlite

from typing import Tuple


class AppData:
    """
    Class for reading and writing AppData to be used between sessions.
    """

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    @property
    def db(self) -> aiosqlite.Connection:
        """
        Database connection.

        Returns:
            Database connection object

        """
        return self._db

    async def _make_query_table(self, name):
        query = f'''
            CREATE TABLE IF NOT EXISTS [{name}] (
                object_id INTEGER PRIMARY KEY,
                timestamp INTEGER NOT NULL
            )
            '''
        await self.db.execute(query)

    async def _make_last_id_table(self):
        query = '''
            CREATE TABLE IF NOT EXISTS queries_last_id (
                query_hash TEXT PRIMARY KEY,
                object_id INTEGER NOT NULL
            )
            '''
        await self.db.execute(query)
        await self.db.commit()

    async def _make_taskgen_table(self, taskgen_name):
        query = f'''
            CREATE TABLE IF NOT EXISTS [{taskgen_name}] (
                task_id TEXT PRIMARY KEY,
                timestamp INTEGER NOT NULL
            )
            '''
        await self.db.execute(query)

    async def add_query_object(self, query_name, object_id, timestamp):
        table_name = f'query_{query_name}'
        await self._make_query_table(table_name)
        query = f'''
            INSERT OR REPLACE INTO {table_name} VALUES (
                ?, ?
            )
            '''
        await self.db.execute(query, (object_id, timestamp))
        await self.db.commit()

    async def add_query_objects(self, query_name, objects: Tuple[Tuple[int, int]]):
        table_name = f'query_{query_name}'
        await self._make_query_table(table_name)
        query = f'''
            INSERT OR REPLACE INTO {table_name} VALUES (
                ?, ?
            )
            '''
        await self.db.executemany(query, objects)
        await self.db.commit()

    async def get_query_objects(self, query_name):
        table_name = f'query_{query_name}'
        await self._make_query_table(table_name)
        query = f'''
            SELECT DISTINCT
                object_id, timestamp
            FROM
                {table_name}
            '''
        async with self.db.execute(query) as cursor:
            return await cursor.fetchall()

    async def has_query_object(self, query_name, object_id) -> bool:
        table_name = f'query_{query_name}'
        await self._make_query_table(table_name)
        query = f'''
            SELECT EXISTS(
                SELECT 
                    1 
                FROM 
                    {table_name} 
                WHERE 
                    task_id="{object_id}"
            )
            '''
        async with self.db.execute(query) as cursor:
            result = await cursor.fetchone()
            return bool(result[0])

    async def add_taskgen_id(self, taskgen_name, task_id, timestamp):
        table_name = f'taskgen_{taskgen_name}'
        await self._make_taskgen_table(table_name)
        query = f'''
            INSERT OR REPLACE INTO {table_name} VALUES (
                ?, ?
            )
            '''
        await self.db.execute(query, (task_id, timestamp))
        await self.db.commit()

    async def add_taskgen_ids(self, taskgen_name, task_ids: Tuple[Tuple[str, int]]):
        table_name = f'taskgen_{taskgen_name}'
        await self._make_taskgen_table(table_name)
        query = f'''
            INSERT OR REPLACE INTO {table_name} VALUES (
                ?, ?
            )
            '''
        await self.db.executemany(query, task_ids)
        await self.db.commit()

    async def get_taskgen_ids(self, taskgen_name):
        table_name = f'taskgen_{taskgen_name}'
        await self._make_taskgen_table(table_name)
        query = f'''
            SELECT DISTINCT
                task_id, timestamp
            FROM
                {table_name}
            '''
        async with self.db.execute(query) as cursor:
            return await cursor.fetchall()

    async def has_taskgen_id(self, taskgen_name, task_id) -> bool:
        table_name = f'taskgen_{taskgen_name}'
        await self._make_taskgen_table(table_name)
        query = f'''
            SELECT EXISTS(
                SELECT 
                    1 
                FROM 
                    {table_name} 
                WHERE 
                    task_id="{task_id}"
            )
            '''
        async with self.db.execute(query) as cursor:
            result = await cursor.fetchone()
            return bool(result[0])

    async def set_last_cursor(self, query_hash, object_id):
        await self._make_last_id_table()
        last_cursor = await self.get_last_cursor(query_hash)
        if all([object_id, last_cursor]) and object_id <= last_cursor:
            return
        query = '''
            INSERT OR REPLACE INTO queries_last_id VALUES (
                ?, ?
            )
            '''
        await self.db.execute(query, (query_hash, object_id))
        await self.db.commit()

    async def get_last_cursor(self, query_hash):
        await self._make_last_id_table()
        query = '''
            SELECT DISTINCT
                object_id
            FROM
                queries_last_id
            WHERE
                query_hash=?
            '''
        async with self.db.execute(query, (query_hash,)) as cursor:
            result = await cursor.fetchone()
        if not result:
            return
        return result[0]
