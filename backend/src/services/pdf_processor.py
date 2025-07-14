import os
import json
import base64
from services.extractor import extract_pdf
from services.analyzer import AzureOpenAIClient
from services.embedding import AzureOpenAIEmClient
from config.config import get_parameter
from common.blob_client import download_blob, upload_to_blob, generate_sas_url
from common.logger import get_logger


logger = get_logger("pdf_processor")

class AzureOpenAIClient:
    def __init__(self):
        self.container = get_parameter("azure.blob.chatbot_container")
        self.container = 
        self.container = 
        self.container = 
    def process_pdf_from_blob(blob_pdf_name: str):
        logger.info(f"Start processing the PDF: {blob_pdf_name}")

        local_pdf_path = os.path.join(get_parameter("paths.input_pdf_dir"), blob_pdf_name)
        download_blob(blob_pdf_name, local_pdf_path)

        # 创建输出目录
        output_dir = "/tmp/output"
        os.makedirs(output_dir, exist_ok=True)
        txt_dir = os.path.join(output_dir, "txt")
        img_dir = os.path.join(output_dir, "images")
        os.makedirs(txt_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)

        # 提取图像和文字
        images, texts = extract_pdf(local_pdf_path)

        analyzer = AzureOpenAIClient()
        embedding = AzureOpenAIEmClient()
        vector_metadata_list = []
        sas_image_urls = []

        for page_num, base64_img in enumerate(images):
            if not base64_img:
                logger.warning(f"第{page_num + 1}页无图片，跳过")
                continue

            # 保存本地图片
            local_image_path = os.path.join(img_dir, f"{page_num + 1}.png")
            with open(local_image_path, "wb") as f:
                f.write(base64.b64decode(base64_img.split(",")[1]))

            # 上传图片到 Blob，并生成 SAS URL
            image_blob_path = f"output/images/{blob_pdf_name}_{page_num + 1}.png"
            upload_to_blob(local_image_path, image_blob_path)
            image_sas_url = generate_sas_url(
                container_name=get_parameter("azure.blob.container_output"),
                blob_name=image_blob_path,
            )
            sas_image_urls.append(image_sas_url)

            # 分析图像和文本
            analysis_text = analyzer.analyze_image(base64_img, texts[page_num])
            if not analysis_text:
                logger.warning(f"第{page_num + 1}页分析结果为空")
                continue

            # 清洗并解析 JSON
            analysis_text_cleaned = (
                analysis_text.replace("```json", "").replace("```", "").strip()
            )
            try:
                res_json = json.loads(analysis_text_cleaned)
            except Exception as e:
                logger.error(f"第{page_num + 1}页分析结果 JSON 解析失败: {e}")
                continue

            # 保存分析结果为 .txt 文件
            local_txt_path = os.path.join(txt_dir, f"{page_num + 1}.txt")
            with open(local_txt_path, "w", encoding="utf-8") as f:
                f.write(analysis_text_cleaned)

            # 上传分析文本到 Blob
            analysis_blob_path = f"output/txt/{blob_pdf_name}_{page_num + 1}.txt"
            upload_to_blob(local_txt_path, analysis_blob_path)

            # 生成 embedding + 元数据
            embedding_vector, metadata = embedding.get_text_embedding(
                res_json.get("text_content", ""),
                blob_pdf_name,
                res_json.get("brand", ""),
                res_json.get("execution_level", ""),
                res_json.get("placement", ""),
                page_num,
            )

            if embedding_vector is not None and metadata is not None:
                metadata["image_sas_url"] = image_sas_url
                vector_metadata_list.append(
                    {
                        "vector": embedding_vector.tolist(),
                        "metadata": metadata,
                        "page_num": page_num + 1,
                    }
                )

        return {
            "sas_image_urls": sas_image_urls,
            "vector_metadata_list": vector_metadata_list,
        }


if __name__ == "__main__":
    test_pdf_path = "your_pdf_file.pdf"
    images, texts, vectors = process_pdf_from_blob(test_pdf_path)
