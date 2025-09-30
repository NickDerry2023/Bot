import discord
import time
import datetime
import asyncio
import pytz
import aiomysql
from datetime import datetime
from discord.ext import commands
from utils.constants import RiftConstants
from utils.embeds import (
    AboutEmbed,
    AboutWithButtons,
    PingCommandEmbed,
    PrefixEmbed,
    PrefixSuccessEmbed,
    PrefixSuccessEmbedNoneChanged,
)
from utils.pagination import PingPaginationView
from utils.utils import RiftContext
from utils.modals import AddUserModal


constants = RiftConstants()

CONTROL_GUILD_ID = 1420889056174411898
CONTROL_ROLE_IDS  = [1421267029960167614, 1421279981220135024]


async def is_panel_admin(discord_id: int) -> bool:
    if not constants.pool:
        await constants.connect()
    async with constants.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id FROM users WHERE oauth_id=%s AND access_level='Developer'",
                (discord_id,),
            )
            row = await cur.fetchone()
            return bool(row)
        
        
def has_any_control_role(member: discord.Member) -> bool:
    user_role_ids = {r.id for r in member.roles}
    return any(rid in user_role_ids for rid in CONTROL_ROLE_IDS)


class CommandsCog(commands.Cog):
    def __init__(self, rift):
        self.rift = rift


    @commands.hybrid_command(
        description="Provides important information about Rift.",
        with_app_command=True,
        extras={"category": "Other"},
    )
    async def about(self, ctx: RiftContext):
        
        await ctx.defer(ephemeral=True)

        uptime_formatted = f"<t:{int((self.rift.start_time.timestamp()))}:R>"
        guilds = len(self.rift.guilds)
        users = sum(g.member_count for g in self.rift.guilds)
        shards = self.rift.shard_count or 1
        cluster = 0
        environment = constants.rift_environment_type() or "Unknown"
        version = await constants.get_mysql_version()
        command_run_time = datetime.now()

        embed = AboutEmbed.create_info_embed(
            uptime=self.rift.start_time,
            guilds=guilds,
            users=users,
            latency=self.rift.latency,
            version=version,
            bot_name=ctx.guild.name,
            bot_icon=ctx.guild.icon,
            shards=shards,
            cluster=cluster,
            environment=environment,
            command_run_time=command_run_time,
            thumbnail_url="https://media.discordapp.net/attachments/1421354662967115928/1421382112833048606/RiftSquareLogo.png?ex=68d8d4bf&is=68d7833f&hm=0bf8d3177eb55c9cd883c1032da6a8d861afbac1157eb735aa15fc20a5b5eb5e&=&format=webp&quality=lossless",
        )

        view = AboutWithButtons.create_view()
        await ctx.send(embed=embed, view=view)


    async def get_db_latency(self):
        
        try:
            start_time = time.time()
            await constants.ping_db()
            db_latency = round((time.time() - start_time) * 1000)
            return db_latency
        
        except Exception as e:
            print(f"Error measuring DB latency: {e}")
            return -1


    @commands.hybrid_command(name="ping", description="Check the bot's latency, uptime, and shard info.", with_app_command=True, extras={"category": "Other"},)
    async def ping(self, ctx: RiftContext):
        
        latency = self.rift.latency
        db_connected = await constants.is_db_connected()
        uptime = self.rift.start_time
        shard_info = []
        
        for shard_id, shard in self.rift.shards.items():
            shard_info.append(
                {
                    "id": shard_id,
                    "latency": round(shard.latency * 1000),
                    "guilds": len([g for g in self.rift.guilds if g.shard_id == shard_id]),
                }
            )

        embed = PingCommandEmbed.create_ping_embed(
            latency, db_connected, uptime, shard_info, page=0
        )
        
        view = PingPaginationView(self.rift, latency, db_connected, uptime, shard_info)
        await ctx.send(embed=embed, view=view)


    @commands.hybrid_command(description="Use this command to say things to people using the bot.", with_app_command=True, extras={"category": "General"},)
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, message: str):
        
        if ctx.interaction:
            await ctx.send("sent", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
            await ctx.channel.send(message, allowed_mentions=discord.AllowedMentions.none())
            
        else:
            await ctx.channel.send(message, allowed_mentions=discord.AllowedMentions.none())
            await ctx.message.delete()


    @commands.hybrid_group(name="add", with_app_command=True, description="This will allow you to add =items using the bot within Discord.")
    async def add(self, ctx: RiftContext):
        if ctx.invoked_subcommand is None:
            return await ctx.send_error("Use a subcommand: `/add owner` or `/add user`.")


    @commands.hybrid_group(name="remove", with_app_command=True, description="This will allow you to remove =items using the bot within Discord.")
    async def remove(self, ctx: RiftContext):
        if ctx.invoked_subcommand is None:
            return await ctx.send_error("Use a subcommand: `/remove owner` or `/remove user`.")


    @add.command(name="owner", description="Grant Developer access to a user.")
    @commands.guild_only()
    async def add_owner(self, ctx: RiftContext, target: discord.User):
        if not ctx.guild or ctx.guild.id != CONTROL_GUILD_ID:
            return await ctx.send_error("This command can only be used in the **Rift Systems** guild.")
        
        if not any(ctx.guild.get_role(rid) for rid in CONTROL_ROLE_IDS):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"None of the configured control roles exist in this guild. Expected one of: {roles_list}"
            )

        if not has_any_control_role(ctx.author):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"You don't have a required role to use this command. You need one of: {roles_list}"
            )
        
        if not await is_panel_admin(ctx.author.id):
            return await ctx.send_error("You don't have panel admin permissions.")

        target_id = target.id
        display = target.mention

        if not constants.pool:
            await constants.connect()

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                
                await cur.execute("SELECT id, access_level FROM users WHERE oauth_id=%s", (target_id,))
                row = await cur.fetchone()
                
                if not row:
                    return await ctx.send_error(f"{display} does not exist in the `users` table (oauth_id={target_id}).")

                if (row.get("access_level") or "").lower() == "developer":
                    return await ctx.send_success(f"{display} is already a **Developer**.")

                await cur.execute(
                    "UPDATE users SET access_level='Developer' WHERE oauth_id=%s",
                    (target_id,)
                )
                
            await conn.commit()

        await ctx.send_success(f"Granted **Developer** access to {display}.")


    @remove.command(name="owner", description="Revoke Developer access.")
    @commands.guild_only()
    async def remove_owner(self, ctx: RiftContext, target: discord.User):
        
        if not ctx.guild or ctx.guild.id != CONTROL_GUILD_ID:
            return await ctx.send_error("This command can only be used in the control guild.")
        
        if not any(ctx.guild.get_role(rid) for rid in CONTROL_ROLE_IDS):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"None of the configured control roles exist in this guild. Expected one of: {roles_list}"
            )

        if not has_any_control_role(ctx.author):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"You don't have a required role to use this command. You need one of: {roles_list}"
            )
        
        if not await is_panel_admin(ctx.author.id):
            return await ctx.send_error("You don't have panel admin permissions.")

        target_id = target.id
        display = target.mention

        if not constants.pool:
            await constants.connect()

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, access_level FROM users WHERE oauth_id=%s", (target_id,))
                
                row = await cur.fetchone()
                
                if not row:
                    return await ctx.send_error(f"{display} does not exist in the `users` table (oauth_id={target_id}).")

                if (row.get("access_level") or "").lower() != "developer":
                    return await ctx.send_success(f"{display} is not a **Developer**.")

                await cur.execute(
                    "UPDATE users SET access_level='User' WHERE oauth_id=%s",
                    (target_id,)
                )
            await conn.commit()

        await ctx.send_success(f"Revoked **Developer** access from {display} (set to **User**).")


    @add.command(name="user", description="Create a panel user for the target.")
    async def add_user(self, ctx: RiftContext, target: discord.User):
        if ctx.interaction is None:
            return await ctx.send_error("Use the **slash** command `/add user` to open the modal.")
        modal = AddUserModal(target_user_id=target.id)
        await ctx.interaction.response.send_modal(modal)


    @remove.command(name="user", description="Remove a panel user for the target")
    async def remove_user(self, ctx: RiftContext, target: discord.User):
        target_id = target.id
        display = target.mention

        if not constants.pool:
            await constants.connect()

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id FROM users WHERE oauth_id=%s", (target_id,))
                row = await cur.fetchone()
                if not row:
                    return await ctx.send_error(f"{display} does not exist in the `users` table (oauth_id={target_id}).")

                await cur.execute(
                    """
                    UPDATE users
                    SET status='Terminated',
                        status_reason='Removed by admin',
                        status_date=CURDATE()
                    WHERE oauth_id=%s
                    """,
                    (target_id,)
                )
            await conn.commit()

        await ctx.send_success(f"Marked **{display}** as **Terminated**.")


async def setup(rift):
    await rift.add_cog(CommandsCog(rift))

# hi