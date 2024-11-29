import gradio as gr
import requests
import base64
import random
from PIL import Image, ImageDraw
from io import BytesIO

title = "PaddleOCR 可视化界面"
# OCR 服务的主机地址
host = "http://ocr:8866"

# 解析 OCR 结果，并绘制检测框（填充内部）
def draw_boxes(image, results):
    draw = ImageDraw.Draw(image, "RGBA")  # 使用 RGBA 模式支持透明度
    for result in results:
        text_region = result["text_region"]

        # 随机生成颜色
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        # 透明度设置为 128 (50%)
        fill_color = (*color, 128)

        # 绘制有透明度的填充背景
        draw.polygon([tuple(point) for point in text_region], fill=fill_color)

        # 绘制检测框
        draw.polygon([tuple(point) for point in text_region], outline=color)
    return image

# 计算中心点
def calculate_center(text_region):
    x_coords = [point[0] for point in text_region]
    y_coords = [point[1] for point in text_region]
    center_x = sum(x_coords) // len(x_coords)
    center_y = sum(y_coords) // len(y_coords)
    return center_x, center_y

# 处理 OCR 识别的请求
def process_image(image_base64):
    # 发送 POST 请求到 OCR 服务
    json_data = {'images': [image_base64]}
    try:
        response = requests.post(
            f"{host}/predict/ocr_system", 
            json=json_data, 
            timeout=20, 
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        return None, [], f"请求出错: {e}"
    total_seconds = response.elapsed.total_seconds()
    response = response.json()

    # 检查响应状态
    if response.get("status") != "000":
        return None, [], f"OCR识别失败: {response.get('msg')}"

    # 提取 OCR 结果
    results = response.get("results", [[]])[0]

    # 返回 OCR 结果
    return results, total_seconds

def ocr_test(image=None, image_base64_str="", image_url=""):
    if not (image or image_base64_str.strip() or image_url.strip()):
        return None, [], "请上传图片、输入图片的 base64 字符串或 URL"

    # 优先处理 image
    if image is not None:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 如果没有 image，处理 base64 字符串
    elif image_base64_str.strip():
        image_base64 = image_base64_str.strip()
        # 将 base64 转换为图片以便后续绘制检测框
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))

    # 如果没有 image 和 base64 字符串，处理 URL
    elif image_url.strip():
        try:
            response = requests.get(image_url.strip(), timeout=10)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            else:
                return None, [], f"无法从 URL 加载图片，HTTP 状态码: {response.status_code}"
        except Exception as e:
            return None, [], f"从 URL 加载图片时出错: {e}"

    # 发送 OCR 请求并获取结果
    ocr_results, total_seconds = process_image(image_base64)
    if not ocr_results:
        return None, [], "OCR识别失败或无结果"

    # 绘制检测框
    result_image = draw_boxes(image.copy(), ocr_results)

    # 生成表格数据
    table_data = [
        [
            res["text"],                                # 识别文本
            res["confidence"],                          # 置信度
            calculate_center(res["text_region"]),       # 中心点 (x, y)
            str(res["text_region"]),                    # 文本区域格式化
        ]
        for res in ocr_results
    ]

    return result_image, table_data, f"识别成功\t耗时: {total_seconds:.2f}s"

# Gradio 界面设计
with gr.Blocks() as demo:
    demo.title = title
    gr.Markdown(f"# {title}")
    
    with gr.Row():
        image_input = gr.Image(height=276, type="pil", label="上传图片")
        with gr.Group():
            base64_input = gr.Textbox(lines=6, label="图片Base64")
            url_input = gr.Textbox(label="图片URL")
    
    with gr.Row():
        run_button = gr.Button("识别")
    
    with gr.Row():
        result_image = gr.Image(label="识别结果图")
        result_table = gr.DataFrame(
            headers=["识别文本", "置信度", "中心点", "文本区域"], 
            label="识别结果"
        )
    
    output_text = gr.Textbox(label="状态信息", interactive=False)

    # 绑定按钮事件
    run_button.click(
        ocr_test, 
        inputs=[image_input, base64_input, url_input], 
        outputs=[result_image, result_table, output_text]
    )

# 启动 Gradio
demo.launch()
