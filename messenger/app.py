from starlette.applications import Starlette
from starlette.routing import WebSocketRoute, Mount
from starlette.websockets import WebSocket
from starlette.staticfiles import StaticFiles
from datetime import datetime
from coolname import generate_slug
import logging

history = []
active_clients = []

async def broadcast_message(msg):
    logging.info('Broadcasting to {} clients', len(active_clients))
    for client in active_clients:
        try:
            await client.send_json(msg)
        except Exception:
            pass

async def socket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    this_client_id = generate_slug(2)
    
    active_clients.append(websocket)
    
    await websocket.send_json({
        'type': 'state',
        'state': 'connected',
        'id': this_client_id
    })
    
    await websocket.send_json({
        'type': 'history',
        'history': history
    })
    
    print('Connected client:', this_client_id)

    try:
        while True:
            msg = await websocket.receive_json()
            if msg['type'] == 'message':
                message = {
                    'sender': this_client_id,
                    'date': datetime.utcnow().timestamp(),
                    'text': msg['message']
                }
                history.append(message)
                await broadcast_message({
                    'type': 'message_broadcast',
                    'body': message
                })
                print('Message {} received from client with id {}'.format(msg['message'], this_client_id))
            else:
                print('Unknown message type received from client {}: {}'.format(this_client_id, msg))
    except Exception as e:
        active_clients.remove(websocket)
        print(f'Client {this_client_id} closed')

app = Starlette(debug=True, routes=[
    WebSocketRoute('/channel', socket_endpoint),
    Mount('/static', StaticFiles(directory='public'))
])
