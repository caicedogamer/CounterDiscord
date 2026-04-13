import discord
from discord import app_commands
from discord.ext import commands
from bot.ml import activity, clusters, anomaly, emoji_trends
from bot.charts import bar

class MLInsightsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="predict-active", description="Predict who will be active today")
    async def predict_active(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            predictions = await activity.predict_active_members(interaction.guild_id, top_n=10)
            if predictions is None:
                await interaction.followup.send(
                    "Not enough data yet to make predictions — need at least 20 users and several days of history."
                )
                return

            labels = []
            values = []
            for _, row in predictions.iterrows():
                member = interaction.guild.get_member(int(row["user_id"]))
                if member:
                    labels.append(member.display_name)
                else:
                    try:
                        member = await interaction.guild.fetch_member(int(row["user_id"]))
                        labels.append(member.display_name)
                    except Exception:
                        labels.append(f"User {str(row['user_id'])[-4:]}")
                values.append(round(float(row["activity_probability"]) * 100, 1))

            buf = await bar.horizontal_bar(
                labels=labels,
                values=values,
                title="Predicted Active Members Today",
                xlabel="Probability (%)",
            )
            await interaction.followup.send(
                content="Members most likely to be active today:",
                file=discord.File(buf, filename="predictions.png")
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

    @app_commands.command(name="user-archetypes", description="Cluster server members by behavior")
    async def user_archetypes(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            result = await clusters.train_and_cluster(interaction.guild_id)
            if result is None:
                await interaction.followup.send("Not enough members to cluster yet.")
                return

            icons = {
                "Power User":      "⚡",
                "Casual Chatter":  "💬",
                "Lurker":          "👻",
                "Weekend Warrior": "🎉",
                "Voice Regular":   "🎙️",
            }

            lines = ["**Member Archetypes**\n"]
            for archetype, group in result.groupby("archetype"):
                icon = icons.get(archetype, "👤")
                lines.append(f"{icon} **{archetype}** — {len(group)} members")
                for _, row in group.iterrows():
                    member = interaction.guild.get_member(int(row["user_id"]))
                    if member:
                        name = member.display_name
                    else:
                        try:
                            member = await interaction.guild.fetch_member(int(row["user_id"]))
                            name = member.display_name
                        except Exception:
                            name = f"User {str(row['user_id'])[-4:]}"
                    lines.append(f"┣ {name}")
                lines[-1] = lines[-1].replace("┣", "┗", 1)  # cap last entry
                lines.append("")

            await interaction.followup.send("\n".join(lines))
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

    @app_commands.command(name="activity-spikes", description="Detect unusual activity spikes")
    async def activity_spikes(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            spikes = await anomaly.detect_activity_spikes(interaction.guild_id)
            if not spikes:
                await interaction.followup.send(
                    "No unusual activity detected, or not enough data yet (need at least 48 hours of history)."
                )
                return

            lines = ["**Detected Activity Spikes**\n"]
            for spike in spikes[:5]:
                hour = spike["hour"].strftime("%a %b %d, %H:00 UTC")
                lines.append(
                    f"📈 `{hour}` — **{spike['message_count']}** messages (z-score: {spike['z_score']:.1f})"
                )
            await interaction.followup.send("\n".join(lines))
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

    @app_commands.command(name="emoji-trends", description="See which emojis are trending")
    async def emoji_trend(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            trends = await emoji_trends.predict_emoji_trends(interaction.guild_id)
            if not trends:
                await interaction.followup.send("Not enough emoji data yet.")
                return

            trend_icons = {"rising": "📈", "falling": "📉", "stable": "➡️"}
            lines = ["**Emoji Trends**\n"]
            for t in trends:
                name = f":{t['emoji_name']}:" if t["emoji_name"] else t["emoji_id"]
                icon = trend_icons[t["trend"]]
                lines.append(
                    f"{icon} **{name}** — {t['trend']} ({t['avg_daily']}/day avg, slope: {t['slope']})"
                )
            await interaction.followup.send("\n".join(lines))
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(MLInsightsCommands(bot))
