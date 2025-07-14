import os
import re
import uuid
import io
import json
import fitz
import time
import functools
import datetime as dt
import pandas as pd
from PIL import Image, UnidentifiedImageError
from typing import List, Dict, Callable, Any
from contextlib import contextmanager
from chardet import detect
from config.config import get_parameter
from src.common.logger import get_logger


logger = get_logger("utils")


def get_sys_timestamp():
    return dt.datetime.now().strftime("%Y%m%d%H%M%S%f")


def is_empty_str(s):
    if pd.isnull(s) or len(s.strip()) == 0:
        return True
    return False


def create_folder_if_not_exists(path_key: str, folder_name: str):
    try:
        folder_path = get_parameter(path_key)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Cannot create {folder_name} folder! Error: {e}")


def detect_encoding(raw_data: bytes) -> str:
    result = detect(raw_data)
    encoding = result["encoding"]
    return encoding or "utf-8"


def parse_blob_data(blob_name: str, raw_data: bytes):
    ext = blob_name.lower().split(".")[-1]
    byte_stream = io.BytesIO(raw_data)
    try:
        if ext in ["xlsx", "xls"]:
            return pd.read_excel(byte_stream)

        elif ext in ["csv"]:
            encoding = detect_encoding(raw_data)
            text = raw_data.decode(encoding)
            return pd.read_csv(io.StringIO(text))

        elif ext in ["json"]:
            encoding = detect_encoding(raw_data)
            text = raw_data.decode(encoding)
            return json.loads(text)

        elif ext in ["txt"]:
            encoding = detect_encoding(raw_data)
            return raw_data.decode(encoding)

        elif ext in ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]:
            return Image.open(byte_stream)

        elif ext == "pdf":
            return fitz.open(stream=raw_data, filetype="pdf")

        else:
            logger.warn(f"Unsupported file type: {blob_name}")
            raise ValueError(f"Unsupported file type: {blob_name}")
    except (
        pd.errors.ParserError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        UnidentifiedImageError,
        fitz.fitz.FileDataError,
        ValueError,
    ) as e:
        logger.error(f"Failed to parse blob data for file: {blob_name}", e)
        raise ValueError(f"Failed to parse file [{blob_name}]: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error while parsing file: {blob_name}", e)
        raise ValueError(f"Unexpected error while parsing file [{blob_name}]: {str(e)}")


def parse_local_file(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    return parse_blob_data(file_path, data)


def split_products(text: str) -> list:
    blocks = re.split(r"(CODE TBD.*?)\n", text)
    products = []
    for i in range(1, len(blocks), 2):
        title = blocks[i].strip()
        body = blocks[i + 1].strip() if i + 1 < len(blocks) else ""
        full = f"{title}\n{body}"
        products.append(full)
    return products


def read_txt_and_build_docs(txt_folder, image_folder):
    def make_fake_sas_url(file_name):
        return f"http://localhost/images/{file_name}"

    all_docs = []

    for txt_file in os.listdir(txt_folder):
        if not txt_file.endswith(".txt"):
            continue

        txt_path = os.path.join(txt_folder, txt_file)
        with open(txt_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        brand = data.get("brand", "")
        execution_level = data.get("execution_level", "")
        placement = data.get("placement", "")
        text_content = data.get("text_content", "")
        base_file_name = data.get("file_name", "no_name.png").replace(".png", "")
        products = data.get("products", [])
        split_texts = split_products(text_content)

        for idx, prod in enumerate(products):
            product_text = split_texts[idx] if idx < len(split_texts) else ""
            auto_image_file_name = f"{base_file_name}_{idx+1}.png"
            image_sas_url = make_fake_sas_url(auto_image_file_name)

            doc = {
                "id": f"{txt_file.replace('.txt', '')}_{idx+1}",
                "brand": brand,
                "execution_level": execution_level,
                "placement": placement,
                "text_content": product_text,
                "product_info": prod,
                "image_sas_url": image_sas_url,
            }
            all_docs.append(doc)

    return all_docs


def read_json_and_build_docs(json_folder: str) -> List[Dict]:
    all_docs = []
    for json_file in os.listdir(json_folder):
        if not json_file.endswith(".json"):
            continue

        json_path = os.path.join(json_folder, json_file)

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                documents = json.load(f)

                for doc in documents:
                    required_fields = [
                        "id",
                        "file_name",
                        "page",
                        "ocr_text",
                        "merged_content",
                        "is_product_page",
                        "is_product_page_reason",
                        "product_brand",
                        "product_execution_level",
                        "product_placement",
                        "product_type",
                        "product_size",
                        "product_PCSBU",
                        "product_PCSSKU",
                        "product_SKUBU",
                        "product_image",
                        "product_image_url",
                    ]

                    for field in required_fields:
                        if field not in doc:
                            doc[field] = None

                    all_docs.append(doc)

        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
            continue

    return all_docs


def save_doc_as_json(docs, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for doc in docs:
        file_id = doc.get("id", "unknown")
        file_path = os.path.join(output_dir, f"{file_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)


def save_to_json(data, output_dir, filename=None, timestamp=True, indent=2):
    try:
        os.makedirs(output_dir, exist_ok=True)

        if not filename:
            base_name = "json"
        else:
            base_name = filename.rsplit(".", 1)[0]

        if timestamp:
            timestamp_str = get_sys_timestamp()
            file_name = f"{base_name}_{timestamp_str}.json"
        else:
            file_name = f"{base_name}.json"

        full_path = os.path.join(output_dir, file_name)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

        print(f"结果已保存至: {full_path}")
        return full_path

    except Exception as e:
        print(f"保存JSON失败: {str(e)}")
        return None


def timed_method(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_time
        logger.info(f"TIMING: {func.__qualname__} executed in {elapsed:.4f} seconds")
        return result

    return wrapper


@contextmanager
def timed_block(name: str):
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        logger.info(f"TIMING: {name} executed in {elapsed:.4f} seconds")
