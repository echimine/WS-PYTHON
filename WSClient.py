import websocket
from Message import Message, MessageType
from Context import Context
import threading
# faire une machine à etat pour le client WebSocket pour la connexion 
# assuré qu'on soit connecter + boucle while pour l'input pour les utilisateur client 1 et client 2
class WSClient:
    def __init__(self, context, client_name):
       self.client_name = client_name
       self.ws = websocket.WebSocketApp(
        context.url(),
        on_open=self.on_open,
        on_message=self.on_message,
        on_error=self.on_error,
        on_close=self.on_close,
    )

    def on_message(self, ws, message):
        print(f"[server] {message}")
        #messageToSend = Message(MessageType.ENVOI, emmiter=self.client_name, content="j'envoie un message à personne", dest="") # remplacer dest par reicever
        #ws.send(messageToSend.to_json())

    def on_error(self, ws, error):
        print(f"[error] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"[close] code={close_status_code} msg={close_msg}")

    def close(self):
        self.ws.close()

    def on_open(self, ws):
        print("[open] connecté")
        message = Message(MessageType.DECLARATION, emmiter=self.client_name, content="", dest="")
        ws.send(message.to_json())

    def connect(self):
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

    def send(self, content, dest):
        message = Message(MessageType.ENVOI, emmiter=self.client_name, content=content, dest=dest)
        self.ws.send(message.to_json())


if __name__ == "__main__":
    # c1 = WSClient(context=Context.dev(), client_name="Romain")
    # c1.connect()

        print("Rentre ton nom")
        emit = input()
        c = WSClient(context=Context.prod(), client_name=emit)
        c.connect()

        print("a qui veut tu envoyer ton message ?")
        dest = input()

        while True:
            print("Quel est ton message ?")
            content = input()
            #print("nom =", emit, "dest =",dest,"content =",content)
            c.send(content, dest)
            

# en prod mettre cette adresse :
    # 192.168.4.138