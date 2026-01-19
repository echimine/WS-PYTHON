import json

class MessageType:
    DECLARATION = "declaration"
    ENVOI = "envoi"
    RECEPTION = "reception"



class Message:
    def __init__(self,type, emmiter, content, dest = None):
        self.emmiter = emmiter
        self.content = content
        self.dest = dest
        self.type = type


    @staticmethod
    def from_json(json_data):
        data = json.loads(json_data)
        type = data['message_type']
        emitter = data['data']['emitter']
        dest = data['data'].get('receiver', None)
        content = data['data']['value']

        return Message(type, emitter, content, dest)
    

    def to_json(self):
        data = {
            'message_type': self.type,
            'data': {
                'emitter': self.emmiter,
                'receiver': self.dest,
                'value': self.content
            }
        }
        return json.dumps(data)
    
#message = Message(type=MessageType.DECLARATION, emmiter="System", content="this is jsp", dest="all")
#messageRebuild = Message.from_json(message.to_json())

