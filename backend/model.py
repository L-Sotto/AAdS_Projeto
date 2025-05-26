class User:
    def __init__(self,user_id,name,password):
        self.user_id=user_id
        self.name = name
        self.password = password

    def to_json(self):
        return {'user_id': self.user_id,'name': self.name,'password' : self.password}
