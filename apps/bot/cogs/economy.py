import discord
from discord.ext import commands
from discord import app_commands
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models.economy import EconomyProfile
from sqlalchemy import select
from datetime import datetime, timedelta
import random
import asyncio

# Define Games Logic Separately

class BlackjackGame:
    def __init__(self, bot, interaction, amount, profile, db):
        self.bot = bot
        self.interaction = interaction
        self.amount = amount
        self.profile = profile
        self.db = db
        
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(self.deck)
        
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]

    def draw_card(self):
        return self.deck.pop()

    def calculate_score(self, hand):
        score = sum(hand)
        aces = hand.count(11)
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

    def create_embed(self, reveal_dealer=False):
        p_score = self.calculate_score(self.player_hand)
        
        if reveal_dealer:
            d_score = self.calculate_score(self.dealer_hand)
            d_hand_str = f"{self.dealer_hand} ({d_score})"
        else:
            d_hand_str = f"[{self.dealer_hand[0]}, ?]"
            
        embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.blue())
        embed.add_field(name="Your Hand", value=f"{self.player_hand} ({p_score})", inline=True)
        embed.add_field(name="Dealer's Hand", value=d_hand_str, inline=True)
        embed.set_footer(text=f"Bet: {self.amount} TL")
        return embed

    async def update_message(self, interaction):
        embed = self.create_embed()
        await interaction.edit_original_response(embed=embed)

    async def end_game(self, interaction, result):
        embed = self.create_embed(reveal_dealer=True)
        
        if result == "win" or result == "dealer_bust":
            self.profile.balance += self.amount
            embed.color = discord.Color.green()
            embed.description = "**YOU WIN!** 🏆" if result == "win" else "**DEALER BUST! YOU WIN!** 🏆"
        elif result == "loss" or result == "bust":
            self.profile.balance -= self.amount
            embed.color = discord.Color.red()
            embed.description = "**YOU LOSE.** 💸" if result == "loss" else "**BUST! YOU LOSE.** 💸"
        elif result == "push":
            embed.color = discord.Color.gold()
            embed.description = "**PUSH!** (Tie)"
            
        embed.add_field(name="New Balance", value=f"{self.profile.balance} TL", inline=False)
        await self.db.commit()
        # Keep db open? No, good practice to close if created locally.
        # But session was created in Cog command. We'll close there? No, we passed it here.
        # Ideally, we should close it here if we are done.
        # However, View might still exist? No, we remove view.
        await interaction.edit_original_response(embed=embed, view=None)

class BlackjackView(discord.ui.View):
    def __init__(self, player_id, game_logic):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.game = game_logic
        self.finished = False

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.success)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id: return
        
        await interaction.response.defer()
        card = self.game.draw_card()
        self.game.player_hand.append(card)
        
        if self.game.calculate_score(self.game.player_hand) > 21:
            self.finished = True
            await self.game.end_game(interaction, "bust")
            self.stop()
        else:
            await self.game.update_message(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id: return
        
        await interaction.response.defer()
        self.finished = True
        
        # Dealer turn
        while self.game.calculate_score(self.game.dealer_hand) < 17:
            self.game.dealer_hand.append(self.game.draw_card())
            
        dealer_score = self.game.calculate_score(self.game.dealer_hand)
        player_score = self.game.calculate_score(self.game.player_hand)
        
        if dealer_score > 21:
            result = "dealer_bust"
        elif dealer_score > player_score:
            result = "loss"
        elif dealer_score < player_score:
            result = "win"
        else:
            result = "push"
            
        await self.game.end_game(interaction, result)
        self.stop()

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.max_bet = 200000

    async def get_profile(self, db, guild_id: str, user_id: str):
        stmt = select(EconomyProfile).where(
            EconomyProfile.guild_id == guild_id, 
            EconomyProfile.user_id == user_id
        )
        profile = (await db.execute(stmt)).scalar_one_or_none()
        if not profile:
            profile = EconomyProfile(guild_id=guild_id, user_id=user_id, balance=0)
            db.add(profile)
        return profile

    @app_commands.command(name="daily", description="Claim your daily reward (500-1000 TL)")
    async def daily(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as db:
            profile = await self.get_profile(db, str(interaction.guild_id), str(interaction.user.id))
            
            now = datetime.utcnow()
            if profile.last_daily and now - profile.last_daily < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - profile.last_daily)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await interaction.response.send_message(f"⏳ You can claim your daily in **{hours}h {minutes}m**.", ephemeral=True)
            
            reward = random.randint(500, 1000)
            profile.balance += reward
            profile.last_daily = now
            await db.commit()
            
            await interaction.response.send_message(f"💰 You claimed **{reward} TL**! New balance: **{profile.balance} TL**")
            
    @app_commands.command(name="balance", description="Check your wallet balance")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        async with AsyncSessionLocal() as db:
            profile = await self.get_profile(db, str(interaction.guild_id), str(target.id))
            await interaction.response.send_message(f"💳 **{target.name}**'s Balance: **{profile.balance:.2f} TL**")

    @app_commands.command(name="coinflip", description="Bet on coinflip (Max 200k TL)")
    @app_commands.describe(amount="Amount to bet", choice="heads or tails")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, amount: int, choice: str):
        if amount <= 0:
            return await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        if amount > self.max_bet:
            return await interaction.response.send_message(f"❌ Max bet limit is **{self.max_bet} TL**!", ephemeral=True)

        async with AsyncSessionLocal() as db:
            profile = await self.get_profile(db, str(interaction.guild_id), str(interaction.user.id))
            
            if profile.balance < amount:
                return await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
                
            outcome = random.choice(["heads", "tails"])
            won = outcome == choice
            
            if won:
                profile.balance += amount
                result_text = f"Outcome: **{outcome.capitalize()}** 🏆 You won **{amount} TL**!"
                color = discord.Color.green()
            else:
                profile.balance -= amount
                result_text = f"Outcome: **{outcome.capitalize()}** 💸 You lost **{amount} TL**."
                color = discord.Color.red()
                
            await db.commit()
            
            embed = discord.Embed(title="🪙 Coin Flip", description=result_text, color=color)
            embed.set_footer(text=f"New Balance: {profile.balance} TL")
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="blackjack", description="Play Blackjack (Max 200k TL)")
    async def blackjack(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        if amount > self.max_bet:
            return await interaction.response.send_message(f"❌ Max bet limit is **{self.max_bet} TL**!", ephemeral=True)

        db = AsyncSessionLocal()
        try:
            profile = await self.get_profile(db, str(interaction.guild_id), str(interaction.user.id))
            
            if profile.balance < amount:
                await db.close()
                return await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
            
            # Start Game Logic
            game = BlackjackGame(self.bot, interaction, amount, profile, db)
            
            embed = game.create_embed()
            view = BlackjackView(interaction.user.id, game)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await db.close()
            raise e

async def setup(bot):
    await bot.add_cog(Economy(bot))
