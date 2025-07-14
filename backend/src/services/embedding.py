import os
import numpy as np
from openai import AzureOpenAI
from datetime import datetime
from config.config import get_parameter
from common.logger import get_logger

logger = get_logger("embedding")


class AzureOpenAIEmClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=get_parameter("azure.gpt.azure_oai_key"),
            api_version_em=get_parameter("azure.gpt.azure_api_version_em"),
            azure_endpoint=get_parameter("azure.gpt.azure_oai_endpoint"),
        )

    def get_text_embedding(
        self,
        text: str,
        file_path: str,
        brand: str,
        execution_level: str,
        placement: str,
        page_index: int,
    ):
        logger.info(f"generating embedding for the number{page_index+1}...")
        try:
            response = self.client.embeddings.create(
                model=get_parameter("azure.gpt.azure_oai_deployment_embedding"),
                input=text,
            )
            embedding = response.data[0].embedding
            metadata = {
                "brand": brand,
                "execution_level": execution_level,
                "placement": placement,
                "text_content": text,
                "page_num": page_index + 1,
                "timestamp": str(datetime.now()),
            }
            logger.info(f"Successfully processed page {page_index + 1}")
            return np.array(embedding), metadata
        except Exception as e:
            logger.error(f"Embedding error at page {page_index + 1}: {str(e)}")
            return None, None
