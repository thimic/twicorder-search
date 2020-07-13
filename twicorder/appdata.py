#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiosqlite


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

    async def add_query_object(self, query_name, object_id, timestamp):
        await self._make_query_table(query_name)
        query = f'''
            INSERT OR REPLACE INTO {query_name} VALUES (
                ?, ?
            )
            '''
        await self.db.execute(query, (object_id, timestamp))
        await self.db.commit()

    async def add_query_objects(self, query_name, objects):
        await self._make_query_table(query_name)
        query = f'''
            INSERT OR REPLACE INTO {query_name} VALUES (
                ?, ?
            )
            '''
        await self.db.executemany(query, objects)
        await self.db.commit()

    async def get_query_objects(self, query_name):
        await self._make_query_table(query_name)
        query = f'''
            SELECT DISTINCT
                object_id, timestamp
            FROM
                {query_name}
            '''
        async with self.db.execute(query) as cursor:
            return await cursor.fetchall()

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
            SELECT
            DISTINCT
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
