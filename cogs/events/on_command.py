import discord
import logging

from discord.ext import commands
from utils.embeds import OnCommandEmbed

class OnCommand(commands.Cog):
    def __init__(self, rift):
        self.rift = rift

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):        
        log_channel_id = 1421575045813370890
        channel = self.rift.get_channel(log_channel_id)
    
        embed = OnCommandEmbed.create_on_command_embed(
            ctx,
            command_name = ctx.command.qualified_name,
            timestamp = ctx.message.created_at,
        )

        await channel.send(embed=embed)
            
async def setup(rift):
    await rift.add_cog(OnCommand(rift))