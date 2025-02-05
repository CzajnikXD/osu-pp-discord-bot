import discord

# The InputModal class is responsible for handling modal form input.
# It handles on_submit and on_error events.
class InputModal(discord.ui.Modal):
    """A modal dialog for user input to enter a page number within a specified range."""

    def __init__(self, max_value, interaction, callback):
        super().__init__(title="Enter Page Number")

        self.max_value = max_value
        self.callback = callback
        self.interaction = interaction

        self.text_input = discord.ui.TextInput(
            label=f"Enter target page number (1-{max_value})",
            placeholder=1,
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle the submission of the modal form."""
        try:
            value = int(self.text_input.value)
            if 1 <= value <= self.max_value:
                if self.callback:
                    await self.callback(interaction, value)
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            else:
                await interaction.response.send_message(f"**Number must be between 1 and {self.max_value}.**", ephemeral=True)
        except:
            await interaction.response.send_message("**Please enter a valid number.**", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Handle any errors that occur during form submission."""
        await interaction.response.send_message("An error occurred.", ephemeral=True)