import os
from waitress import serve
from app import create_app
if __name__=='__main__':
    serve(create_app(),host='127.0.0.1',port=int(os.environ.get('BRIDGEND_PORT','8767')),threads=4,max_request_body_size=8*1024*1024,clear_untrusted_proxy_headers=True)
