# PaddleOCR-docker

端口 `8866`
```
import requests

json_data = {
    'images': ['image_base64'],
}

response = requests.post('http://127.0.0.1:8866/predict/ocr_system', json=json_data)
```

### Gradio 可视化界面
端口 `7860`

### RUN
```
docker-compose up -d
```
