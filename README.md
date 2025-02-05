<p align="center">
  <img src="https://imgur.com/mW5xuP6.png" alt="External image">
</p>

# **Simple osu discord bot**
This bot is a project I started because the old osu! Discord bot I was using began calculating performance points incorrectly after the major osu! pp calculation revamp.

## **Implemented Functionality**
- Calculates performance points for osu! Standard mode (compatible with both Stable and Lazer builds).
- Downloads beatmapsets used by players locally and sorts them by usage (default map storage limit is 5GB, which can be changed in the code).
- Stores osu! usernames and their preferred osu! build locally, and calculates pp based on this information.

## **Setup**
To run the bot yourself you need to:
- Provide all of .env variables:
  - DISCORD_TOKEN 
  - CLIENT_ID
  - CLIENT_SECRET
- Install all dependencies from requirements.txt
