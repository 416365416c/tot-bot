# LAD is the Logic Abstraction of Discord
# All discord specific calls in logic.py are broken out to this interface to allow independent testing

class Lad:
    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.guild_id = None
        self.guild = None

    def set_guild(self, guild_id):
        # Must be a guild that it has been added to!
        self.guild_id = None
        self.guild = None
        if type(guild_id) == str:
            try:
                guild_id = int(guild_id)
            except:
                return
            
        for guild in self.discord_client.guilds:
            if guild.id == guild_id:
                self.guild_id = guild.id
                self.guild = guild
                return

    def guild_name(self):
        if self.guild_id == None or self.guild == None:
            return None
        return self.guild.name

    def get_role_name_or_id(self, role_id=None, role_name=None):
        if self.guild == None:
            return None
        roles = self.guild.roles
        if role_id:
            try:
                role_id = int(role_id)
            except:
                return None
            for r in roles:
                if r.id == role_id:
                    return r.name
        elif role_name:
            for r in roles:
                if r.name == role_name:
                    return r.id
        return None

    def get_user_name_or_id(self, user_id=None, user_name=None):
        if self.guild == None:
            return None
        members = self.guild.members
        if user_id:
            member = self.guild.get_member(user_id)
            if member:
                return member.name
        elif user_name:
            member = self.guild.get_member_named(user_name)
            if member:
                return member.id
        return None

    def get_user_roles(self, user_id):
        if self.guild == None:
            return []
        member = self.guild.get_member(int(user_id))
        ret = []
        if member:
            for r in member.roles:
                ret.append(r.id)
        return ret

    def dm(self, user_id, message):
        member = self.guild.get_member(user_id)
        member.send(message) # No waiting, just let it run in the background

class FakeLad:
    def __init__(self):
        self.guild_id = 11

    def set_guild(self, guild_id):
        self.guild_id = guild_id

    def guild_name(self):
        return "Fake Guild"

    def get_role_name_or_id(self, role_id=None, role_name=None):
        if role_name == "Fake Role":
            return 2
        elif role_id == 2:
            return "Fake Role"
        return None

    def get_user_name_or_id(self, user_id=None, user_name=None):
        if user_name == "Fake User":
            return 9
        elif user_id == 9:
            return "Fake User"
        elif user_name == "Ace":
            return 1
        elif user_id == 1:
            return "Ace"
        return None

    def get_user_roles(self, user_id):
        return [2]

    def dm(self, user_id, message):
        self.fake_dm = f"{self.get_user_name_or_id(user_id=user_id)}: {message}"

    def pop_last_dm(self):
        """ Only in FakeLad, for testing purposes """
        ret = self.fake_dm
        self.fake_dm = None
        return ret
