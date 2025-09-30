# ==========================================================================================================
# This file is for Roblox related word filtering, this might later be merged with roblox.py
# ==========================================================================================================

import os
import discord
import aiohttp
from discord.ext import commands
from utils.constants import RiftConstants

constants = RiftConstants()

# Load Roblox cookie from environment (.env file)
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
ROBLOX_USER_ID = os.getenv("ROBLOX_USER_ID")

class RobloxFilter(commands.Cog):
    def __init__(self, rift: commands.Bot):
        self.rift = rift

    async def roblox_filter(self, text: str, under13: bool = False) -> str | None:
        url = "https://textfilter.roblox.com/v1/filter-text"
        payload = {
            "text": text,
            "context": "Chat",
            "userId": ROBLOX_USER_ID,
            "chatMode": "Under13" if under13 else "Over13"
        }

        headers = {
            "Cookie": ROBLOX_COOKIE,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
            return data.get("filteredText")
        except Exception:
            return None

    @commands.command(name="filter")
    async def filter_word(self, ctx: commands.Context, word: str = None, age: str = None):
        # Maintenance lock
        embed = discord.Embed(
            title="<:riftsystems:1421319259472003212> Roblox Chat Filter",
            description="<:RiftFail:1421378112339312742> Sorry, this command is currently under maintenance. Please try again later.",
            color=0x89FFBC
        )
        return await ctx.send(embed=embed)



async def setup(rift: commands.Bot):
    await rift.add_cog(RobloxFilter(rift))
