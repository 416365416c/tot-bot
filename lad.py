# LAD is the Logic Abstraction of Discord
# All discord specific calls in logic.py are broken out to this interface to allow independent testing

class Lad:
    def __init__(self, discord_client):
        self.discord_client = discord_client
        #self.guild_id = None
        #self.guild = None

    def get_guild(self, guild_id):
        return None

    def set_guild(self, guild_id):
        # Trying just using all guilds instead
        return None

        # Must be a guild that it has been added to!
        #self.guild_id = None
        #self.guild = None
        #if type(guild_id) == str:
        #    try:
        #        guild_id = int(guild_id)
        #    except:
        #        return
        #    
        #for guild in self.discord_client.guilds:
        #    if guild.id == guild_id:
        #        self.guild_id = guild.id
        #        self.guild = guild
        #        return
    def guild_name(self):
        if self.discord_client == None:
            return None
        return self.discord_client.guilds[0].name

    def get_role_name_or_id(self, role_id=None, role_name=None):
        if self.discord_client == None:
            return None
        roles = []
        for guild in self.discord_client.guilds:
            roles += guild.roles

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
        if self.discord_client == None:
            return None

        for guild in self.discord_client.guilds:
            if user_id:
                member = guild.get_member(user_id)
                if member:
                    return member.name
            elif user_name:
                member = guild.get_member_named(user_name)
                if member:
                    return member.id
        return None

    def get_user_roles(self, user_id):
        if self.discord_client == None:
            return None

        ret = []
        for guild in self.discord_client.guilds:
            member = guild.get_member(int(user_id))
            if member:
                for r in member.roles:
                    ret.append(r.id)
        return ret

    def all_with_role(self, role_name):
        if self.discord_client == None:
            return []
        ret = []
        for guild in self.discord_client.guilds:
            for member in guild.members:
                for role in member.roles:
                    if role.name == role_name:
                        ret.append(member.name)
        return ret

    async def dm(self, user_id, message):
        if self.discord_client == None:
            return None
        member = None
        for guild in self.discord_client.guilds:
            member = guild.get_member(int(user_id))
            if member:
                break
            
        if member:
            await member.send(message) # TODO: No waiting, just let it run in the background
        else:
            print(f"Skipping message for {user_id} as they are no longer associated")

class FakeLad:
    def __init__(self):
        self.guild_id = 11
        self.fake_dm = None

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

    def all_with_role(self, role_name):
        return ["Fake User"]

    def get_user_roles(self, user_id):
        return [2]

    async def dm(self, user_id, message):
        self.fake_dm = f"{self.get_user_name_or_id(user_id=user_id)}: {message}"

    def pop_last_dm(self):
        """ Only in FakeLad, for testing purposes """
        ret = self.fake_dm
        self.fake_dm = None
        return ret
