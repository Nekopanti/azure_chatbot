import time
from openai import AzureOpenAI
from config.config import get_parameter
from common.logger import get_logger

logger = get_logger("analyzer")


class AzureOpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=get_parameter("azure.gpt.azure_oai_key"),
            api_version=get_parameter("azure.gpt.azure_api_version"),
            azure_endpoint=get_parameter("azure.gpt.azure_oai_endpoint"),
        )

    def analyze_image(self, base64_image: str, text: str) -> str:
        system_prompt = """
你是一个专业的视觉内容分析助手，对Point of Sale (POS)有很深的理解，擅长从图像中识别品牌信息、营销物料设计风格、投放位置及文字内容。
你的任务是理解用户上传的 Point of Sale (POS) 材料图片内容，并按照指定的 JSON格式输出关键信息。
"""
        user_prompt = """
请分析我上传的这张图片，它是一张 Point of Sale（销售点）营销物料。你需要从中识别以下信息并以严格的 JSON 格式返回，不要任何额外解释或格式：

1. brand:（品牌名称）
2. execution_level:（执行层级，例如：标准 / 本地定制 / 高端展示）
3. placement:（投放位置，例如：收银台 / 展架 / 货架边 / 入口处）
4. text_content:（图片中的原始文字内容，保持原样）
5. file_name:（图片的名字）
6. Size:（图片中的产品的size）
7. Branding:（图片中的产品的Branding）
8. PCS/BU:（图片中的产品的PCS/BU）
9. PCS/SKU:（图片中的产品的PCS/SKU）
10. SKU/BU:（图片中的产品的SKU/BU）

注意：
1.如果某些信息无法从图中判断，请留空。
2.输出必须为标准 JSON 格式，使用英文键名，值为英文。
3. 一张图片中有多种产品，需要全部识别，并返回。
"""

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=get_parameter("azure.gpt.azure_oai_deployment_gpt"),
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": base64_image},
                                },
                            ],
                        },
                    ],
                    max_tokens=3000,
                    top_p=0.1,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warn(f"调用Azure OpenAI接口失败，尝试{attempt + 1}，错误: {e}")
                time.sleep(retry_delay)

        logger.error("调用Azure OpenAI接口失败，超过最大重试次数")
        return ""
