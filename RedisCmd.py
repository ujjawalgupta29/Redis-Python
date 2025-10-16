class RedisCmd:
    cmd = ""
    args = []
    
    def __init__(self, cmd, args):
        self.cmd = cmd
        self.args = args