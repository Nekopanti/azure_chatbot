import os
from src.common.utils import (
    read_txt_and_build_docs,
    save_doc_as_json,
    save_to_json,
    read_json_and_build_docs,
)
from src.common.logger import get_logger
from src.common.vectorizer import AzureAISearchVectorizer
from src.common.posm_service_azure import NaturalLanguageQASystem
from config.config import get_parameter


logger = get_logger("run_test")

if __name__ == "__main__":
    # txt_folder = get_parameter("paths.output_txt_dir")
    # json_folder = get_parameter("paths.input_json_dir")
    # image_folder = get_parameter("paths.output_image_dir")

    # docs = read_json_and_build_docs(json_folder)
    # docs = read_txt_and_build_docs(txt_folder, image_folder)
    # vector = AzureAISearchVectorizer(
    #     get_parameter("azure.ai_search.azure_search_index")
    # )
    # vector.vectorize_and_upload(docs)
    # print(vector.search_azureindex)
    # save_doc_as_json(docs, get_parameter("paths.output_json_dir"))

    qa_system = NaturalLanguageQASystem(
        search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME")
    )
    # results = qa_system.test()

    # docs = list(results)

    # print(f"[DEBUG] Total results: {len(docs)}")
    # for doc in docs:
    #     save_doc_as_json(docs, get_parameter("paths.output_json_dir"))
    # print(doc)
    summary = "I'm looking for a 43x38cm Aperol display stand with a logo"
    result = qa_system.generate_title(summary)
    print(f"{result}")
    # questions = [
    #     "Show me Aperol backpacks with orange branding",
    # ]
    # # "Find Aperol tote bags with size 43x38 cm and PCS/BU of 100",
    # # "Basic level product"
    # # "Show me Aperol backpacks with orange branding",
    # # "What's the price for Aperol tote bags?",
    # # "Find products with size around 40x35 cm and SKU/BU of 10",
    # for question in questions:
    #     result = qa_system.ask_question(question)

    # print(f"\n{'='*50}")
    # print(f"Question: {question}")
    # print(f"Answer: {result['answer']}")
    #     print(f"Sources: {result['sources']}")
    #     print(f"Relevant docs: {result['relevant_docs_count']}")

    # save_to_json(result, get_parameter("paths.output_json_dir"))
