
from websocket_server import WebsocketServer
from Context import Context
from Message import Message, MessageType
class WSServer: 
    def __init__(self, context):
        self.port = context.port
        self.host = context.host
        self.server = WebsocketServer(host=self.host, port=self.port, loglevel=1)
        self.server.set_fn_new_client(self.on_new_client)
        self.server.set_fn_client_left(self.on_client_left)
        self.server.set_fn_message_received(self.on_message_received)

        self.clients = {}

    def on_new_client(self,client, server):
        print(f"[+] Client connecté: id={client['id']} addr={client['address']}")
        server.send_message(client, "Bienvenue !")

    def on_client_left(self, client, server):
        print(f"[-] Client déconnecté: id={client['id']}")

    def on_message_received(self, client, server, message):
        print(f"[{client['id']}] {message}")
        received_message = Message.from_json(message)
        if received_message.type == MessageType.DECLARATION:
            server.send_message(client, f"declaration reçue de {received_message.emmiter}")
            self.clients[received_message.emmiter] = client
        elif received_message.type == MessageType.ENVOI:
            received_client = self.clients.get(received_message.dest, None)
            if received_client:
                server.send_message(received_client, f"Message de [{received_message.emmiter}]: {received_message.content}")
            else:
                server.send_message(client, f"Erreur: destinataire {received_message.dest} non trouvé.")



    def start(self):
        print(f"Serveur WS sur ws://{self.host}:{self.port}")
        self.server.run_forever()



if __name__ == "__main__":  
    s = WSServer(Context.prod())
    s.start()