import dataclasses
import typing

import discord
import motor.motor_asyncio

import model.persona


class DataStore:
    def __init__(self, url, db_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(url)
        self._db: motor.motor_asyncio.AsyncIOMotorDatabase = self._client[db_name]
        self._messages = self._get_collection("messages")
        self._links = self._get_collection("links")
        self._personas = self._get_collection("personas")

    def _get_collection(self, collection_name: str):
        return self._db[collection_name]

    async def save_message(self, message: discord.Message):
        channel = message.channel
        channel_name = "dm" if isinstance(channel, discord.DMChannel) else channel.name

        payload = {
            "channel": channel_name,
            "sender": message.author.name,
            "message": message.content,
            "time": message.created_at,
        }
        if message.guild:
            payload["server"]: message.guild.name

        await self._messages.insert_one(payload)

    async def save_link(self, message: discord.Message):
        await self._links.insert_one({
            "server": message.guild.name,
            "channel": message.channel.name,
            "sender": message.author.name,
            "link": message.content,
            "time": message.created_at,
        })

    async def add_persona(self, persona: model.persona.Persona):
        await self._personas.insert_one(dataclasses.asdict(persona))

    async def update_persona(self, name, new_description):
        await self._personas.update_one(
            {"name": name},
            {"$set": {"description": new_description}}
        )

    async def delete_persona(self, name):
        await self._personas.delete_one({"name": name})

    async def get_persona(self, name):
        doc = await self._personas.find_one({"name": name})
        if doc:
            return model.persona.Persona(doc["name"], doc["description"])
        else:
            return None

    async def list_personas(self) -> typing.AsyncIterable[model.persona.Persona]:
        async for doc in self._personas.find():
            yield model.persona.Persona(
                doc["name"],
                doc["description"],
            )