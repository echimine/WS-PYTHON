# client_ws.py
import time
import websocket

URL = "ws://127.0.0.1:8765"

def on_message(ws, message):
    print(f"[server] {message}")

def on_error(ws, error):
    print(f"[error] {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[close] code={close_status_code} msg={close_msg}")

def on_open(ws):
    print("[open] connecté")

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Boucle réseau dans un thread (pas d'async/await)
    ws.run_forever(dispatcher=None, reconnect=0)

    # Variante alternative si tu veux envoyer en "mode blocant":
    # (voir plus bas)
