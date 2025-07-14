import uuid
import re
from typing import List, Dict
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    HnswParameters,
)
from openai import AzureOpenAI
from config.config import get_parameter
from src.common.logger import get_logger

logger = get_logger("vectorizer")


class AzureAISearchVectorizer:
    def __init__(
        self,
        search_index_name: str,
    ):
        self.embedding_model = get_parameter("azure.gpt.azure_oai_deployment_embedding")
        self.search_index_name = search_index_name

        self.client = AzureOpenAI(
            api_key=get_parameter("azure.gpt.azure_oai_key"),
            azure_endpoint=get_parameter("azure.gpt.azure_oai_endpoint"),
            api_version=get_parameter("azure.gpt.azure_api_version_em"),
        )
        self.search_client = SearchClient(
            endpoint=get_parameter("azure.ai_search.azure_search_endpoint"),
            index_name=search_index_name,
            credential=AzureKeyCredential(
                get_parameter("azure.ai_search.azure_search_key")
            ),
        )
        self.index_client = SearchIndexClient(
            endpoint=get_parameter("azure.ai_search.azure_search_endpoint"),
            credential=AzureKeyCredential(
                get_parameter("azure.ai_search.azure_search_key")
            ),
        )

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def prepare_documents(self, docs: List[Dict]) -> List[Dict]:
        texts = [doc["ocr_text"] for doc in docs]
        embeddings = self.generate_embeddings(texts)

        formatted_docs = []
        for i, doc in enumerate(docs):
            document = {
                "@search.action": "upload",
                "id": doc.get("id", str(uuid.uuid4())),
                "ocr_text": doc.get("ocr_text", ""),
                "merged_content": doc.get("merged_content", ""),
                "embedding": embeddings[i],
                "file_name": doc.get("file_name", ""),
                "page": doc.get("page", 0),
                "is_product_page": doc.get("is_product_page", False),
                "is_product_page_reason": doc.get("is_product_page_reason", ""),
                "product_brand": doc.get("product_brand", ""),
                "product_execution_level": doc.get("product_execution_level", ""),
                "product_placement": doc.get("product_placement", ""),
                "product_type": doc.get("product_type", ""),
                "product_size": doc.get("product_size", ""),
                "product_PCSBU": doc.get("product_PCSBU", ""),
                "product_PCSSKU": doc.get("product_PCSSKU", ""),
                "product_SKUBU": doc.get("product_SKUBU", ""),
                "product_image": doc.get("product_image", ""),
                "product_image_url": doc.get("product_image_url", ""),
            }
            formatted_docs.append(document)

        return formatted_docs

    def upload_documents(self, documents: List[Dict]) -> None:
        try:
            if documents:
                first_doc_fields = list(documents[0].keys())
                logger.info(f"Document fields: {first_doc_fields}")
                for field in ["Size", "Branding", "PCSBU", "PCSSKU", "SKUBU"]:
                    if field in first_doc_fields:
                        logger.error(
                            f"Found invalid field '{field}' - should be 'product_info_{field}'"
                        )
                        raise ValueError(f"Document contains invalid field '{field}'")
            result = self.search_client.upload_documents(documents=documents)
            logger.info(f"Upload result: {result}")
        except Exception as e:
            logger.error(f"Upload to Azure AI Search failed: {e}")
            raise

    def vectorize_and_upload(self, docs: List[Dict]) -> None:
        formatted_docs = self.prepare_documents(docs)
        self.create_or_update_azureindex(formatted_docs)

    def create_or_update_azureindex(self, documents: List[Dict]) -> None:
        try:
            self.index_client.get_index(self.search_index_name)
            self.index_client.delete_index(self.search_index_name)
            logger.info(f"Index {self.search_index_name} was deleted")
        except ResourceNotFoundError:
            logger.info(f"Index {self.search_index_name} did not exist.")
        except Exception as e:
            logger.error(f"Error deleting index {self.search_index_name}: {e}")

        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                searchable=False,
                retrievable=True,
            ),
            SimpleField(
                name="file_name",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SimpleField(
                name="page",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True,
                retrievable=True,
            ),
            SearchableField(
                name="ocr_text",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="merged_content",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SimpleField(
                name="is_product_page",
                type=SearchFieldDataType.Boolean,
                filterable=True,
                retrievable=True,
            ),
            SearchableField(
                name="is_product_page_reason",
                type=SearchFieldDataType.String,
                retrievable=True,
            ),
            SearchableField(
                name="product_brand",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="product_execution_level",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="product_placement",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="product_type",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
                searchable=True,
                retrievable=True,
            ),
            SimpleField(
                name="product_image",
                type=SearchFieldDataType.String,
                retrievable=True,
            ),
            SimpleField(
                name="product_image_url",
                type=SearchFieldDataType.String,
                retrievable=True,
            ),
            SearchableField(
                name="product_size",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(name="product_PCSBU", type=SearchFieldDataType.String),
            SearchableField(name="product_PCSSKU", type=SearchFieldDataType.String),
            SearchableField(name="product_SKUBU", type=SearchFieldDataType.String),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                retrievable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="vector-profile-0618",
            ),
        ]
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config-0618",
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric="cosine",
                    ),
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile-0618",
                    algorithm_configuration_name="hnsw-config-0618",
                )
            ],
        )
        # SimpleField(
        #     name="content",
        #     type=SearchFieldDataType.String,
        #     searchable=True,
        #     retrievable=True,
        # ),
        # SimpleField(
        #     name="type",
        #     type=SearchFieldDataType.String,
        #     searchable=True,
        #     filterable=True,
        #     retrievable=True,
        # ),

        index = SearchIndex(
            name=self.search_index_name, fields=fields, vector_search=vector_search
        )
        self.index_client.create_or_update_index(index)
        logger.info(f"Index {self.search_index_name} created.")

        self.upload_documents(documents)

    def search_azureindex(self):
        results = self.search_client.search(search_text="*")
        all_contents = [result["text_content"] for result in results]
        return all_contents
