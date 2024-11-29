FROM python:3.10-slim

ENV TZ=Asia/Shanghai
WORKDIR /app
COPY app.py .
RUN pip install --no-cache-dir gradio requests pillow
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "app.py"]
