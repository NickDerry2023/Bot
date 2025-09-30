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
# ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
ROBLOX_COOKIE = "CAEaAhAB.80FAF33CC93168100334183FF7D89CA5A3EA23829C448F0D542FFF04BE66AD544535D52566D9D95DB05FE10871658B494B04F3E411658B66B2869FA523D0F9068AA9244E857739B08379A0534A7F8F4B5C4E0E06D5BF754602C869AE568557D3B9A3C90FDE9CBC4ADB1DB4529668CE71F9DCA347E2CF207FFBC2BB89AA703E22AEA71AEB385227F2418428459C240B7F264DE66762775F718BF751A7AE72F313AE5D8AC34AF13DE62D23347B40D3A15A50AFE8BA75832FF74447D3FD3F7EA0611A5291E1CAFC3A6B4C49BE0EEBD54869B1B7F75C9BE72B215CFCF11D04D5BC0C5540693ED5F804A5DC9813E67711126EBF337DD56342583E4B9ABBCD7A43D08F11C2704A20ADA0C455DF3CF54121E645C1D9AD9BB9934EE1E2A0307818824C155798E8DBB4769CFF93B3A7FF84C3C2C602E56C4D231724E605FD58183686D19160390D1B4A1A2BFED1C4477A26911128828772F1E2EA396555C1AD9A17DB787752FCC2D150071BF19F6A15B6F4915BFFA9CD0D25532E5833E502BBFAC88CEBF8F01510535ABB22B985F519AC59CC0408DF5202497E008A06C2093CC166C3E2373289A3B811DF97C6882FA079D808DBBD7D9C2200C57284A04E4033DC0B50893443723D8DBEFB14A43586E37E6EF73758F390BF5AE50D2D416AB115FCEAA62B0DF4FD525547A907B82B5435B932D231218500ABADACDCE421D22AA817BEC4ABC7C43CC41AD7508E23D6B3DAA15B6466942D9F3D58755B142B0DD592C081771130D4303F0F4A3AE0AEF5B1E9713E69538456D221AEFC01B631F5DD896FDE385A0E1D8D63EA1590D8F66A4ECB769FFB42E890544D960F1D99351722E79F1C83781AF540C1BBC6D6B705F4DDF61ACC318B9A582EA7F22CD9AC5E1D04D800D08A03FB03ECD014A373124A2EEECE2B917AE0070345ECE65048594FFFFDC2E88C081B52444221F957E9DBE07AD12FB1A3CFF0916C9AFDCF7926742DFDD2D38C446A87D9CBCE81D524E5F91989B223FBF27D53EE99E6315852F2EE104C8AEF2501E34B1B1313867B8A3BC5BDC90B22BC0D03F5E2D34DC11CA821E4C40B0320D0FFD991FF8DFDFD743F2F089DA77553EDD8606F81D25B67CD4EFBC3D3B09E5C4EC9ABF9F01958AE162E83BB589A8918C77DB86806B0F26BFABDD9EBCDCA2E7D8AE1ADDF21F8020FD661FAE7B4BD6C4F9E3036CB3A9CD5827A"
ROBLOX_USER_ID = 9613555137

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
