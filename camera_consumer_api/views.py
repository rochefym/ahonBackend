import requests
from django.http import StreamingHttpResponse

# Create your views here.
def stream_camera(request):
    """Minimal Django view to stream ESP32 camera"""
    
    def generate():
        try:
            response = requests.get('http://172.29.9.200:81/stream', stream=True)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        except:
            yield b"Camera offline"
    
    return StreamingHttpResponse(
        generate(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )