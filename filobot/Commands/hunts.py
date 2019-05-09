import json
import os
import logging
import sys
import discord
import typing

from discord.ext import commands
from filobot.utilities import hunt_embed
from filobot.utilities.manager import HuntManager


class Hunts(commands.Cog):

    def __init__(self, bot: discord.ext.commands.Bot, hunt_manager: HuntManager):
        self._log = logging.getLogger(__name__)
        self.bot = bot

        self.hunt_manager = hunt_manager

        with open(os.path.dirname(os.path.realpath(sys.argv[0])) + os.sep + os.path.join('data', 'marks_info.json')) as json_file:
            self.marks_info = json.load(json_file)

    @commands.command()
    async def info(self, ctx: commands.context.Context, *, name: str):
        """
        Return information on the specified hunt target
        """
        try:
            embed = hunt_embed(name)
        except KeyError:
            await ctx.send("No hunt by that name found - please check your spelling and try again")
            return

        await ctx.send(embed=embed)

    @commands.command()
    async def status(self, ctx: commands.context.Context, world: str, *, hunt_name: str):
        """
        Retrieve the status of the specified hunt target
        """
        # Make sure the world is properly formatted
        world = world.lstrip().rstrip().lower().title()
        hunt_name = hunt_name.lstrip().rstrip().lower()

        try:
            horus, xivhunt = self.hunt_manager.get(world, hunt_name)
            embed = hunt_embed(hunt_name, horus, xivhunt)
        except KeyError as e:
            self._log.info(e)
            await ctx.send(
                "No world or hunt by that name found on the Crystal DC - please check your spelling and try again"
            )
            return

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sub(self, ctx: commands.context.Context, world: str, category: str, *, conditions: typing.Optional[str] = 'all'):
        """
        Subscribe the channel to hunt events
        Allowed categories: SB_A, SB_S, HW_A, HW_S, ARR_A, ARR_S
        Allowed conditions: FINDS, DEATHS, OPENINGS
        """
        await self.hunt_manager.subscribe(ctx.channel.id, world, category, conditions)

    @commands.command(name='sub-all')
    @commands.has_permissions(administrator=True)
    async def sub_all(self, ctx: commands.context.Context, category: str, *, conditions: typing.Optional[str] = 'all'):
        """
        Subscribe the channel to hunt events on ALL Crystal DC worlds
        Allowed categories: SB_A, SB_S, HW_A, HW_S, ARR_A, ARR_S
        Allowed conditions: FINDS, DEATHS, OPENINGS
        """
        await self.hunt_manager.subscribe_all(ctx.channel.id, category, conditions)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unsub(self, ctx: commands.context.Context, world: str, category: str):
        """
        Subscribe the channel to hunt events
        Allowed categories: SB_A, SB_S, HW_A, HW_S, ARR_A, ARR_S
        """
        await self.hunt_manager.unsubscribe(ctx.channel.id, world, category)

    @commands.command(name='sub-list')
    @commands.has_permissions(administrator=True)
    async def sub_list(self, ctx: commands.context.Context):
        """
        List all enabled subscriptions for this channel
        """
        try:
            subs = await self.hunt_manager.get_subscriptions(ctx.channel.id)
        except KeyError as e:
            self._log.info(e)
            await ctx.channel.send(
                    "No subscriptions have been specified for this channel"
            )
            return

        await ctx.send('```' + str(subs) + '```')

    @commands.command(name='sub-clear')
    @commands.has_permissions(administrator=True)
    async def sub_clear(self, ctx: commands.context.Context):
        """
        Clear all enabled subscriptions for this channel
        """
        try:
            await self.hunt_manager.clear_subscriptions(ctx.channel.id)
        except KeyError as e:
            self._log.info(e)
            await ctx.channel.send(
                    "No subscriptions have been specified for this channel"
            )
            return

        await ctx.send("Subscriptions for this channel have been cleared")