from .. import configs

from .guild import Guild
from .base import DiscordModelsBase
from flask import current_app, session
from .connections import UserConnection


class User(DiscordModelsBase):
    """Class representing Discord User.

    Attributes
    ----------
    id : int
        The discord ID of the user.
    username : str
        The discord username of the user.
    discriminator : str
        4 length string representing discord tag of the user.
    avatar_hash : str
        Hash of users avatar.
    bot : bool
        A boolean representing whether the user belongs to an OAuth2 application.
    mfa_enabled : bool
        A boolean representing whether the user has two factor enabled on their account.
    locale : str
        The user's chosen language option.
    verified : bool
        A boolean representing whether the email on this account has been verified.
    email : str
        User's email ID.
    flags : int
        An integer representing the
        `user flags <https://discordapp.com/developers/docs/resources/user#user-object-user-flags>`_.
    premium_type : int
        An integer representing the
        `type of nitro subscription <https://discordapp.com/developers/docs/resources/user#user-object-premium-types>`_.
    connections : list
        A list of :py:class:`flask_discord.UserConnection` instances. These are cached and this list might be empty.

    """

    ROUTE = "/users/@me"

    def __init__(self, payload):
        super().__init__(payload)
        self.id = int(self._payload["id"])
        self.username = self._payload["username"]
        self.discriminator = self._payload["discriminator"]
        self.avatar_hash = self._payload.get("avatar", self.discriminator)
        self.bot = self._payload.get("bot", False)
        self.mfa_enabled = self._payload.get("mfa_enabled")
        self.locale = self._payload.get("locale")
        self.verified = self._payload.get("verified")
        self.email = self._payload.get("email")
        self.flags = self._payload.get("flags")
        self.premium_type = self._payload.get("premium_type")

        # Few properties which are intended to be cached.
        self._guilds = dict()         # Mapping of guild ID to flask_discord.models.Guild(...).
        self.connections = list()     # List of flask_discord.models.UserConnection(...).

    @property
    def guilds(self):
        """A cached mapping of user's guild ID to :py:class:`flask_discord.Guild`. The guilds are cached when the first
        API call for guilds is requested so it might be an empty dict.

        """
        return list(self._guilds.values())

    def __str__(self):
        return f"{self.name}#{self.discriminator}"

    @property
    def name(self):
        """An alias to the username attribute."""
        return self.username

    @property
    def avatar_url(self):
        """A property returning direct URL to user's avatar."""
        image_format = configs.DISCORD_ANIMATED_IMAGE_FORMAT \
            if self.is_avatar_animated else configs.DISCORD_IMAGE_FORMAT
        return configs.DISCORD_USER_AVATAR_BASE_URL.format(
            user_id=self.id, avatar_hash=self.avatar_hash, format=image_format)

    @property
    def is_avatar_animated(self):
        """A boolean representing if avatar of user is animated. Meaning user has GIF avatar."""
        return self.avatar_hash.startswith("a_")

    def add_to_guild(self, guild_id) -> dict:
        """Method to add user to the guild, provided OAuth2 session has already been created with ``guilds.join`` scope.

        Parameters
        ----------
        guild_id : int
            The ID of the guild you want this user to be added.
            
        Returns
        -------
        dict
            A dict of guild member object. Returns an empty dict if user is already present in the guild.

        Raises
        ------
        flask_discord.Unauthorized
            Raises :py:class:`flask_discord.Unauthorized` if current user is not authorized.

        """
        data = {"access_token": session["DISCORD_OAUTH2_TOKEN"]["access_token"]}
        headers = {"Authorization": f"Bot {current_app.config['DISCORD_BOT_TOKEN']}"}
        return self._request(
            f"/guilds/{guild_id}/members/{self.id}", method="PUT", oauth=False, json=data, headers=headers
        ) or dict()

    def fetch_guilds(self) -> list:
        """A method which makes an API call to Discord to get user's guilds. It prepares the internal guilds cache
        and returns list of all guilds the user is member of.

        Returns
        -------
        list
            List of :py:class:`flask_discord.Guilds` instances.

        """
        self._guilds = {guild.id: guild for guild in Guild.fetch_from_api()}
        return self.guilds

    def fetch_connections(self) -> list:
        """A method which makes an API call to Discord to get user's connections. It prepares the internal connection
        cache and returns list of all connection instances.

        Returns
        -------
        list
            A list of :py:class:`flask_discord.UserConnection` instances.

        """
        self.connections = UserConnection.fetch_from_api()
        return self.connections


class Bot(User):
    """Class representing the client user itself."""
    # TODO: What is this?
