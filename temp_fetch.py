import requests
import socks
import socket

socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 9150)
socket.socket = socks.socksocket

session = requests.Session()
try:
    response = session.get('http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/', timeout=60)
    print('Status:', response.status_code)
    print('Content length:', len(response.text))
    print('Content:')
    print(repr(response.text))  # use repr to see exact content
except Exception as e:
    print('Error:', e)