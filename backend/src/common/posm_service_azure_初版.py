import os
import re
import json
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from src.common.utils import timed_method, timed_block
from src.common.logger import get_logger

# Initialize logger
logger = get_logger("posm_service_azure")

# Handle compatibility with different Azure SDK versions
try:
    # New SDK version (>=11.4.0b6)
    from azure.search.documents.models import VectorizedQuery

    logger.info("Using VectorizedQuery from new SDK")
except ImportError:
    try:
        # Old SDK version (<11.4.0)
        from azure.search.documents.models import Vector

        logger.info("Using Vector from old SDK")
    except ImportError:
        logger.warn(
            "Both VectorizedQuery and Vector not found. Using dictionary approach"
        )
        Vector = None
        VectorizedQuery = None


class NaturalLanguageQASystem:
    def __init__(self, search_index_name: str):
        self.search_index_name = search_index_name
        self._init_openai_clients()
        self._init_search_client()
        self._init_field_mappings()
        self._init_value_mappings()

    @timed_method
    def _init_openai_clients(self):
        self.embedding_model = os.getenv("AZURE_GPT_DEPLOYMENT_EMBEDDING")
        self.chat_model = os.getenv("AZURE_GPT_DEPLOYMENT_GPT")
        common_params = {
            "api_key": os.getenv("AZURE_GPT_API_KEY"),
            "azure_endpoint": os.getenv("AZURE_GPT_ENDPOINT"),
        }
        self.embedding_client = AzureOpenAI(
            **common_params, api_version=os.getenv("AZURE_GPT_API_VERSION_EM")
        )
        self.chat_client = AzureOpenAI(
            **common_params, api_version=os.getenv("AZURE_GPT_API_VERSION")
        )

    @timed_method
    def _init_search_client(self):
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=self.search_index_name,
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
        )

    @timed_method
    def _init_field_mappings(self):
        self.FIELD_MAPPING = {
            # Brand-related terms
            "brand": "product_brand",
            "manufacturer": "product_brand",
            "label": "product_brand",
            # Execution level terms
            "execution level": "product_execution_level",
            "execution_level": "product_execution_level",
            "priority": "product_execution_level",
            "level": "product_execution_level",
            # Placement terms
            "placement": "product_placement",
            "location": "product_placement",
            "position": "product_placement",
            # Product type terms
            "type": "product_type",
            "product type": "product_type",
            "category": "product_type",
            # Size/dimension terms
            "size": "product_size",
            "dimension": "product_size",
            "measurement": "product_size",
            # Image reference terms
            "image": "product_image_url",
            "picture": "product_image_url",
            "photo": "product_image_url",
            # Quantity terms
            "pcs per bu": "product_PCSBU",
            "bu quantity": "product_PCSBU",
            "pieces per bu": "product_PCSBU",
            "pcs per sku": "product_PCSSKU",
            "sku quantity": "product_PCSSKU",
            "pieces per sku": "product_PCSSKU",
            "sku per bu": "product_SKUBU",
            "bu sku": "product_SKUBU",
            "skus per bu": "product_SKUBU",
        }

        # List of valid fields in the search index
        self.VALID_FIELDS = [
            "product_brand",
            "product_execution_level",
            "product_placement",
            "product_branding",
            "product_type",
            "product_size",
            "product_PCSBU",
            "product_PCSSKU",
            "product_SKUBU",
            "product_image_url",
        ]
        # Fields used for exact match filtering
        self.FILTER_FIELDS = [
            "product_brand",
            "product_execution_level",
            "product_placement",
        ]
        # Relative weights for query terms
        self.KEY_WEIGHTS = {
            "product_brand": 0.75,
            "product_execution_level": 0.7,
            "product_placement": 0.65,
            "product_type": 0.6,
            "product_size": 0.55,
            "product_PCSBU": 0.5,
            "product_PCSSKU": 0.45,
            "product_SKUBU": 0.45,
            "product_branding": 0.45,
            "default": 0.4,
        }
        # Context terms for field disambiguation
        self.FIELD_CONTEXT = {
            "product_execution_level": ["execution", "level", "priority", "lvl"],
            "product_placement": ["placement", "location", "position", "where"],
            "product_brand": ["brand", "manufacturer", "label", "make"],
        }

    @timed_method
    def _init_value_mappings(self):
        # Define value normalization rules for consistent filtering
        self.VALUE_MAPPING = {
            "product_execution_level": {
                "lighthouse": "Lighthouse",
                "lh": "Lighthouse",
                "l": "Lighthouse",
                "light": "Lighthouse",
                "1": "Lighthouse",
                "enhanced": "Enhanced",
                "enh": "Enhanced",
                "e": "Enhanced",
                "2": "Enhanced",
                "standard": "Standard",
                "std": "Standard",
                "s": "Standard",
                "3": "Standard",
                "basic": "Basic",
                "bas": "Basic",
                "b": "Basic",
                "4": "Basic",
            },
            "product_brand": {
                # Brand name normalization mappings
                "multibrand": "Multibrand",
                "aperol": "APEROL",
                "aperol spritz": "Aperol Spritz",
                "campari": "Campari",
                "crodino": "Crodino",
                "bulldog": "Bulldog",
                "bulldog london dry gin": "BULLDOG LONDON DRY GIN",
                "bulldog london dry": "BULLDOG LONDON DRY",
                "braulio": "Braulio",
                "averna": "Averna",
                "amaro averna": "Amaro Averna",
                "amaro averna siciliano": "AMARO AVERNA SICILIANO",
                "cynar": "CYNAR",
                "cinzano": "Cinzano",
                "riccadonna": "Riccadonna",
                "mondoro": "Mondoro",
                "bickens": "Bickens",
                "espolon tequila": "Espolon Tequila",
                "espolon": "Espolon",
                "espólon tequila": "ESPOLÓN TEQUILA",
                "wild turkey": "Wild Turkey",
                "appleton estate": "Appleton Estate",
                "unbranded": "Unbranded",
                "skyy vodka": "SKYY Vodka",
                "wild turkey american honey": "Wild Turkey American Honey",
                "american honey": "AMERICAN HONEY",
                "wild turkey american honey®": "Wild Turkey American Honey®",
                "the glen grant": "The Glen Grant",
                "glengrant": "GLENGRANT",
                "glen grant": "Glen Grant",
                "wray & nephew": "WRAY & NEPHEW",
                "montelobos": "MONTELOBOS",
                "montelobos®": "MONTELOBOS®",
                "montelobos® - mezcal artesanal": "MONTELOBOS® - MEZCAL ARTESANAL",
                "mayenda tequila": "Mayenda Tequila",
                "mayenda": "Mayenda",
                "howler head": "Howler Head",
                "ancho reyes": "Ancho Reyes",
                "grand marnier": "Grand Marnier",
                "lallier": "Lallier",
                "lallier champagne": "Lallier Champagne",
                "bisquit & dubouché": "Bisquit & Dubouché",
                "bisquit & dubouche": "Bisquit & Dubouche",
                "bisquit & dubouche cognac": "Bisquit & Dubouche Cognac",
                "picon": "Picon",
                "campari group": "Campari Group",
                "campari academy": "Campari Academy",
                # Add common case variations
                "multibrand": "Multibrand",
                "aperol": "APEROL",
                "campari": "Campari",
                "crodino": "Crodino",
                "bulldog": "Bulldog",
                "braulio": "Braulio",
                "averna": "Averna",
                "cynar": "CYNAR",
                "cinzano": "Cinzano",
                "riccadonna": "Riccadonna",
                "mondoro": "Mondoro",
                "bickens": "Bickens",
                "espolon": "Espolon",
                "wild turkey": "Wild Turkey",
                "appleton estate": "Appleton Estate",
                "unbranded": "Unbranded",
                "skyy vodka": "SKYY Vodka",
                "glen grant": "Glen Grant",
                "wray & nephew": "WRAY & NEPHEW",
                "montelobos": "MONTELOBOS",
                "mayenda": "Mayenda",
                "howler head": "Howler Head",
                "ancho reyes": "Ancho Reyes",
                "grand marnier": "Grand Marnier",
                "lallier": "Lallier",
                "bisquit & dubouche": "Bisquit & Dubouche",
                "picon": "Picon",
                "campari group": "Campari Group",
            },
            "product_placement": {
                "external": "External",
                "outdoor": "External",
                "outside": "External",
                "internal": "Internal",
                "indoor": "Internal",
                "inside": "Internal",
                "table": "Table/Counter",
                "counter": "Table/Counter",
                "tabletop": "Table/Counter",
                "staff": "Staff",
                "employee": "Staff",
                "personnel": "Staff",
            },
        }

    @timed_method
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = self.embedding_client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    @timed_method
    def ask_question(self, question: str) -> Dict[str, Any]:
        try:
            logger.info(f"Processing question: {question}")

            with timed_block("Total question processing"):
                extraction = self._extract_info(question)
                logger.info(f"Extraction results: {json.dumps(extraction, indent=2)}")

                queries = self._build_queries(question, extraction["keywords"])
                with timed_block("Document search"):
                    context, relevant_docs = self._search_docs(
                        queries,
                        extraction["filters"].get("product_brand"),
                        extraction["filters"].get("product_execution_level"),
                        extraction["filters"].get("product_placement"),
                    )
                with timed_block("Answer generation"):
                    return self._generate_answer(
                        question, context, relevant_docs, extraction
                    )

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return {
                "answer": "Sorry, an error occurred while processing your question",
                "error": str(e),
                "sources": [],
            }

    @timed_method
    def _extract_info(self, question: str) -> Dict[str, Any]:
        # 1. Regularization
        regex_extraction = self._extract_with_regex(question)
        logger.info(
            f"Regex extraction results: {json.dumps(regex_extraction, indent=2)}"
        )

        # 2. Verify the regular extraction results
        validated_regex = self._validate_and_classify_extraction(regex_extraction)
        logger.info(
            f"Validated regex extraction: {json.dumps(validated_regex, indent=2)}"
        )

        # 3. Check if the key fields have been extracted
        key_fields = ["product_brand", "product_execution_level", "product_placement"]
        has_key_fields = any(
            field in validated_regex["filters"] for field in key_fields
        )
        # 4. Call AI extraction
        if has_key_fields:
            logger.info("Key fields found by regex, skipping AI extraction")
            ai_extraction = {"filters": {}, "keywords": {}}
        else:
            ai_extraction = self._extract_with_ai(question)
            logger.info(f"AI extraction results: {json.dumps(ai_extraction, indent=2)}")

        # 5. Merge results
        final_result = self._merge_extractions(validated_regex, ai_extraction)

        return final_result

    @timed_method
    def _extract_with_ai(self, question: str) -> Dict[str, Any]:
        try:
            # Dynamically generate brand prompts
            brand_examples = ", ".join(
                list(self.VALUE_MAPPING["product_brand"].values())[:3]
            )
            system_prompt = f"""
                    You are an expert at extracting product information from user questions.
                    Follow these rules STRICTLY:

                    1. Extract ONLY information EXPLICITLY MENTIONED in the user's question
                    2. NEVER return example values or placeholder data
                    3. If a value is NOT mentioned, DO NOT include it in the output
                    4. Use the EXACT wording from the question when possible
                    5. For filter fields, use ONLY values that match the described patterns

                    Field Definitions:
                    A. Filters (for exact matching):
                    - product_brand: Recognized brand names (e.g., {brand_examples}, etc.)
                    - product_execution_level: MUST be one of: Lighthouse, Enhanced, Standard, Basic
                    - product_placement: MUST be one of: External, Internal, Table/Counter, Staff

                    B. Keywords (for semantic search - any relevant value):
                    - product_size (e.g., dimensions like '43x38 cm' or size descriptions)
                    - product_branding (e.g., branding elements like 'Aperol logo')
                    - product_PCSBU (e.g., quantity per business unit)
                    - product_PCSSKU (e.g., quantity per SKU)
                    - product_SKUBU (e.g., SKUs per business unit)

                    Output format: STRICT JSON with ONLY these two keys:
                    {{
                    "filters": {{"product_brand": "...", "product_execution_level": "...", "product_placement": "..."}},
                    "keywords": {{"product_size": "...", ...}}
                    }}

                    Critical rules for output:
                    1. Include ONLY fields that are explicitly mentioned
                    2. DO NOT include any fields that are not mentioned
                    3. DO NOT use any values from this instruction - use ONLY what's in the user question
                    4. If no filters are found, use empty object: {{}}
                    5. If no keywords are found, use empty object: {{}}
                    6. For filter fields, if the mentioned value doesn't match the described pattern,
                    DO NOT include it in filters

                    Bad example (DO NOT DO THIS):
                    {{"filters":{{"product_brand":"Aperol", "product_placement":"Internal"}}, "keywords":{{}}}}
                    This is bad because 'Internal' is an example value, not from the user

                    Good example for 'Show me Aperol displays with Basic level':
                    {{"filters": {{"product_brand": "Aperol", "product_execution_level": "Basic"}}, "keywords": {{}}}}

                    Good example for 'I need large POSM with 100 pieces per BU':
                    {{"filters": {{}}, "keywords": {{"product_size": "large", "product_PCSBU": "100"}}}}

                    Good example for 'Show me displays for XYZ brand (unrecognized)':
                    {{"filters": {{}}, "keywords": {{"product_brand": "XYZ"}}}}
                    """

            response = self.chat_client.chat.completions.create(
                model=self.chat_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.1,
                max_tokens=600,
                top_p=0.5,
                frequency_penalty=0.2,  # Reduce the possibility of duplicate content
                presence_penalty=0.2,  # Encourage diverse expression
                seed=12345,  # Fix the random seed to ensure consistent results
                timeout=10,  # Set a timeout to prevent long waits
            )

            message = response.choices[0].message.content
            return json.loads(message)
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            return {"filters": {}, "keywords": {}}

    @timed_method
    def _extract_execution_level(self, question: str) -> Optional[str]:
        return self._extract_field("product_execution_level", question)

    @timed_method
    def _extract_placement(self, question: str) -> Optional[str]:
        return self._extract_field("product_placement", question)

    @timed_method
    def _extract_brand(self, question: str) -> Optional[str]:
        return self._extract_field("product_brand", question)

    @timed_method
    def _extract_with_regex(self, question: str) -> Dict[str, str]:
        keywords = {}

        # Use unified extraction method
        if level := self._extract_execution_level(question):
            keywords["product_execution_level"] = level

        if placement := self._extract_placement(question):
            keywords["product_placement"] = placement

        if brand := self._extract_brand(question):
            keywords["product_brand"] = brand

        patterns = {
            "product_size": r"(\d+[xX]\d+\s*cm|\d+\s*cm|\d+\s*mm|\d+\s*in|\d+\s*inch)",
            "product_type": r"(type|product type|category):?\s*([\w\s]+)",
            "product_PCSBU": r"(PCS\/BU|bu quantity|pieces per bu):?\s*(\d+)",
            "product_PCSSKU": r"(PCS\/SKU|sku quantity|pieces per sku):?\s*(\d+)",
            "product_SKUBU": r"(SKU\/BU|bu sku|skus per bu):?\s*(\d+)",
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                value = match.group(2) if len(match.groups()) > 1 else match.group(1)
                keywords[field] = value.strip()

        return keywords

    @timed_method
    def _build_queries(self, question: str, keywords: Dict[str, str]) -> List[Dict]:
        queries = []
        queries.append({"text": question, "weight": 0.8, "type": "main"})
        for key, value in keywords.items():
            weight = self.KEY_WEIGHTS.get(key, self.KEY_WEIGHTS["default"])
            queries.append(
                {"text": f"{key}:{value}", "weight": weight, "type": f"keyword_{key}"}
            )

        if keywords:
            combined = f"{question} {' '.join(keywords.values())}"
            queries.append({"text": combined, "weight": 0.65, "type": "combined"})

        logger.debug(f"Built queries: {[q['type'] for q in queries]}")
        return queries

    @timed_method
    def _search_docs(
        self,
        queries: List[Dict],
        brand: Optional[str],
        execution_level: Optional[str],
        placement: Optional[str],
    ) -> Tuple[str, List[Dict]]:
        try:
            with timed_block("Embedding generation"):
                # 1. Generate embedding vectors for all queries
                embeddings = self._get_embeddings([q["text"] for q in queries])
                for i, q in enumerate(queries):
                    q["vector"] = embeddings[i]
            with timed_block("Candidate document retrieval"):
                # 2. Perform a search to obtain candidate documents
                candidate_docs = self._get_candidate_docs(
                    queries, brand, execution_level, placement
                )

            with timed_block("Document scoring and sorting"):
                # 3. Calculate weighted scores and sort
                scored_docs = self._score_and_sort(queries, candidate_docs)
            with timed_block("Result construction"):
                # 4. Build return results
                return self._build_results(scored_docs)
        except Exception as e:
            logger.error(f"Search documents failed: {str(e)}")
            return "", []

    @timed_method
    def _get_candidate_docs(
        self,
        queries: List[Dict],
        brand: Optional[str],
        execution_level: Optional[str],
        placement: Optional[str],
    ) -> List[Dict]:
        filter_str = self._build_filter(brand, execution_level, placement)

        # Compatible with vector search of different SDK versions
        try:
            vector_queries = []
            for q in queries:
                if VectorizedQuery:
                    vector_queries.append(
                        VectorizedQuery(vector=q["vector"], fields="embedding")
                    )
                elif Vector:
                    vector_queries.append(Vector(value=q["vector"], fields="embedding"))
                else:
                    vector_queries.append(
                        {"vector": q["vector"], "fields": "embedding"}
                    )
            results = self.search_client.search(
                search_text="",
                vector_queries=vector_queries,
                filter=filter_str,
                top=30,
                select=[
                    "embedding",
                    "id",
                    "merged_content",
                    "file_name",
                    "page",
                    "is_product_page",
                    "product_brand",
                    "product_branding",
                    "product_execution_level",
                    "product_placement",
                    "product_type",
                    "product_size",
                    "product_PCSBU",
                    "product_PCSSKU",
                    "product_SKUBU",
                    "product_image_url",
                ],
            )
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

        docs = []
        for result in results:
            doc = dict(result)
            doc["text"] = doc.get("text_content", "")
            docs.append(doc)

        logger.info(f"Retrieved {len(docs)} candidate documents")
        return docs

    @timed_method
    def _build_filter(
        self,
        brand: Optional[str],
        execution_level: Optional[str],
        placement: Optional[str],
    ) -> Optional[str]:
        filters = []
        filters.append("is_product_page eq true")
        if brand:
            brand_field = self.FIELD_MAPPING.get("brand", "product_brand")
            filters.append(f"search.ismatch('{brand}', '{brand_field}')")

        if execution_level:
            level_field = self.FIELD_MAPPING.get(
                "execution level", "product_execution_level"
            )
            filters.append(f"search.ismatch('\"{execution_level}\"', '{level_field}')")
        if placement:
            placement_field = self.FIELD_MAPPING.get("placement", "product_placement")
            filters.append(f"search.ismatch('\"{placement}\"', '{placement_field}')")

        return " and ".join(filters) if filters else None

    @timed_method
    def _score_and_sort(self, queries: List[Dict], docs: List[Dict]) -> List[Dict]:
        if not docs:
            return []
        # Collect raw scores for normalization
        raw_scores = []
        for doc in docs:
            doc_vector = doc.get("embedding")
            if not doc_vector:
                doc["score"] = 0
                raw_scores.append(0)
                continue

            total_score = 0
            for query in queries:
                similarity = self._cosine_similarity(query["vector"], doc_vector)
                total_score += similarity * query["weight"]

            # Save the original score
            doc["raw_score"] = total_score
            raw_scores.append(total_score)

        if raw_scores:
            # Convert to a 2D array for MinMaxScaler
            scores_2d = np.array(raw_scores).reshape(-1, 1)

            # Create and apply a normalizer
            scaler = MinMaxScaler()
            normalized_scores = scaler.fit_transform(scores_2d).flatten()

            # Assign normalized scores
            for i, doc in enumerate(docs):
                doc["score"] = normalized_scores[i]
        else:
            for doc in docs:
                doc["score"] = 0

        sorted_docs = sorted(docs, key=lambda x: x["score"], reverse=True)
        # Dynamic threshold: the more documents, the higher the threshold
        min_threshold = max(0.7, 0.8 - 0.02 * len(sorted_docs))
        filtered_docs = [doc for doc in sorted_docs if doc["score"] >= min_threshold][
            :10
        ]

        if filtered_docs:
            min_score = filtered_docs[-1]["score"]
            max_score = filtered_docs[0]["score"]
            logger.info(
                f"Document score range: {min_score:.2f}-{max_score:.2f} "
                f"(threshold: {min_threshold:.2f}), "
                f"returning {len(filtered_docs)} documents"
            )
        else:
            logger.info("No documents found above threshold")
        return filtered_docs

    @timed_method
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        return float(cosine_similarity([vec_a], [vec_b])[0][0])

    @timed_method
    def _build_results(self, docs: List[Dict]) -> Tuple[str, List[Dict]]:
        context_parts = []
        relevant_docs = []

        for doc in docs:
            context_parts.append(doc["text"])
            relevant_docs.append(
                {
                    "id": doc.get("id", ""),
                    "merged_content": doc.get("merged_content", ""),
                    "brand": doc.get("product_brand", ""),
                    "execution_level": doc.get("product_execution_level", ""),
                    "placement": doc.get("product_placement", ""),
                    "product_type": doc.get("product_type", ""),
                    "file_name": doc.get("file_name", ""),
                    "page": doc.get("page", ""),
                    "branding": doc.get("product_branding", ""),
                    "is_product_page": doc.get("is_product_page", False),
                    "score": doc.get("score", 0),
                    "product_info": {
                        "Size": doc.get("product_size", ""),
                        "Type": doc.get("product_type", ""),
                        "PCSBU": doc.get("product_PCSBU", ""),
                        "PCSSKU": doc.get("product_PCSSKU", ""),
                        "SKUBU": doc.get("product_SKUBU", ""),
                        "image_url": doc.get("product_image_url", ""),
                    },
                }
            )

        return "\n\n".join(context_parts), relevant_docs

    @timed_method
    def _generate_answer(
        self, question: str, context: str, relevant_docs: List[Dict], extraction: Dict
    ) -> Dict:
        prompt = self._build_prompt(question, context, extraction, relevant_docs)
        response = self.chat_client.chat.completions.create(
            model=self.chat_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a product expert that outputs responses in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=3096,
        )
        try:
            ai_response = json.loads(response.choices[0].message.content)
            if not self._validate_ai_response(ai_response):
                raise ValueError("Invalid response format from AI")
            return {
                "answer": ai_response,
                "relevant_docs_count": len(relevant_docs),
            }
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an issue while processing your request. "
                "Please try rephrasing your question or contact support for assistance",
                "relevant_docs_count": 0,
            }

    @timed_method
    def _build_prompt(
        self, question: str, context: str, extraction: Dict, relevant_docs: List[Dict]
    ) -> str:

        MAX_DOCS_IN_PROMPT = 5
        limited_docs = relevant_docs[:MAX_DOCS_IN_PROMPT]
        # Extracted filter conditions
        filters = (
            "\n".join([f"{k}: {v}" for k, v in extraction["filters"].items()])
            or "No filters"
        )

        # Extracted keywords
        keywords = (
            "\n".join([f"{k}: {v}" for k, v in extraction["keywords"].items()])
            or "No keywords"
        )

        sorted_docs = sorted(
            relevant_docs, key=lambda x: x.get("score", 0), reverse=True
        )
        best_match = sorted_docs[0] if sorted_docs else {}
        best_match_summary = (
            (
                f"Brand: {best_match.get('brand', 'N/A')}, "
                f"Size: {best_match.get('product_info', {}).get('Size', 'N/A')}, "
                f"Source: {best_match.get('file_name', 'N/A')} Page {best_match.get('page', 'N/A')}"
            )
            if sorted_docs
            else "N/A"
        )

        # Prepare product information context
        products_context = []
        for i, doc in enumerate(limited_docs, 1):
            products_context.append(
                f"Product {i}: "
                f"ID: {doc.get('id', 'N/A')} | "
                f"Brand: {doc.get('brand', 'N/A')} | "
                f"File: {doc.get('file_name', 'N/A')} | "
                f"Page {doc.get('page', 'N/A')} | "
                f"Execution Level: {doc.get('execution_level', 'N/A')} | "
                f"Placement: {doc.get('placement', 'N/A')} | "
                f"Branding: {doc.get('branding', 'N/A')} | "
                f"Size: {doc.get('product_info', {}).get('Size', 'N/A')} | "
                f"Type: {doc.get('product_info', {}).get('Type', 'N/A')} | "
                f"PCS/BU: {doc.get('product_info', {}).get('PCSBU', 'N/A')} | "
                f"PCS/SKU: {doc.get('product_info', {}).get('PCSSKU', 'N/A')} | "
                f"SKU/BU: {doc.get('product_info', {}).get('SKUBU', 'N/A')} | "
                f"Image URL: {doc.get('product_info', {}).get('image_url', 'N/A')} | "
                f"Product Page: {'Yes' if doc.get('is_product_page') else 'No'} | "
                f"Score: {doc.get('score', 0):.2f}"
            )
        products_text = (
            "\n".join(products_context) if products_context else "No products found"
        )

        return f"""
            ## User Question
            {question}

            ## Extracted Criteria
            {filters}
            {keywords}

            ## Relevant Products (Top {MAX_DOCS_IN_PROMPT} of {len(relevant_docs)})
            {products_text}

            ## Answer Requirements
            You are an expert product advisor. Provide a JSON response with:
            1. Natural language summary answering the question
            2. Structured product details for each match

            ### Response Structure (STRICT JSON FORMAT):
            {{
            "natural_language_response": "Concise answer addressing the question (2-3 sentences)",
            "conclusion": "Match summary including total count and match types (e.g., 'Found {len(relevant_docs)}  products: 2 full matches, 1 partial match')",
            "products": [
                {{
                "id": "Product ID",
                "source_file": "Document name",
                "page": "Page number",
                "brand": "Brand name",
                "branding": "Branding details",
                "execution_level": "Lighthouse/Enhanced/Standard/Basic",
                "placement": "Placement location",
                "size": "Product dimensions",
                "type": "Product type",
                "pcs_bu": "Pieces per BU",
                "pcs_sku": "Pieces per SKU",
                "sku_bu": "SKUs per BU",
                "image_url": "Image URL",
                "is_product_page": true/false,
                "product_summary": "1-2 sentence description highlighting relevance",
                "match_score": 0.0-1.0
                }}
            ],
            "confidence": 0-100,
            "confidence_reason": "Brief justification"
            }}

            ### Critical Rules:
            1. Products MUST be ordered by match_score DESC (best first)
            2. Include ALL products from Relevant Products section
            3. For each product, create a unique product_summary:
            - Highlight key attributes (brand, size, type)
            - Explain relevance to the query
            - Mention source location (file + page)
            4. Natural language response MUST:
            - Start with direct answer
            - Mention key findings (e.g., "I found {len(relevant_docs)} options")
            - Highlight top match: {best_match_summary}
            - Offer further assistance
            5. Use ONLY information from Relevant Products section
            6. Missing fields = "N/A"

            ### Formatting Rules:
            - Output SINGLE VALID JSON object
            - Property names in DOUBLE QUOTES
            - No trailing commas
            - No additional text outside JSON

            ### Product Summary Examples:
            1. "This Aperol display (43x38cm) fully matches your request. It's on page 3 of catalog.pdf with PCS/BU of 100."
            2. "Campari glass set partially matches - correct size but Basic level instead of Standard. See page 5 of barware.pdf."
            3. "Alternative: 40x35cm Aperol display on page 7 of promotions.pdf meets most requirements."

            ### Response Examples:
            Example 1 (Matches found):
            {{
            "natural_language_response": "I found 3 Aperol displays matching your criteria. The best option is a 43x38cm display on page 3 of catalog.pdf with Lighthouse priority. Two additional options are available with similar specs. Let me know if you need more details!",
            "conclusion": "Found 3 products: 1 full match, 2 partial matches",
            ...
            }}

            Example 2 (No exact match):
            {{
            "natural_language_response": "No exact matches, but I found 2 similar Campari displays. The closest is a 40x35cm option on page 7 of promotions.pdf with Enhanced level. Would you like details?",
            "conclusion": "No full matches, 2 partial matches found",
            ...
            }}
            """

    @timed_method
    def _validate_ai_response(self, response: Dict) -> bool:
        required_keys = ["conclusion", "products", "confidence"]
        if not all(key in response for key in required_keys):
            logger.warn(f"Missing required keys: {required_keys}")
            return False
        if not isinstance(response.get("products"), list):
            logger.warn("'products' should be a list")
            return False
        return True

    @timed_method
    def generate_title(self, summary: str) -> Dict[str, Any]:
        ai_title = self._title_with_ai(summary)
        return ai_title

    @timed_method
    def _title_with_ai(self, summary: str, mode: str = "natural") -> Dict[str, Any]:
        try:
            if mode == "natural":
                system_prompt = """
                    You are an assistant that generates short and natural English titles for user queries.
                    Follow this json format strictly: { "title": "your generated title" }

                    Rules:
                    1. Title must be ≤ 3 words.
                    2. Make it natural, like a conversation or document title.
                    3. Preserve key information (e.g., brand, size, intent).
                    4. Avoid symbols or emojis.
                """
            else:
                system_prompt = """
                    You are an assistant that extracts and compresses key terms into a concise title.
                    Follow this json format strictly: { "title": "your generated title" }

                    Rules:
                    1. Title must be ≤ 3 words.
                    2. Focus on core keywords (brand, size, object).
                    3. Do not include filler words, personal pronouns, or emotion.
                    4. Use only English letters, numbers, or spaces.
                """

            response = self.chat_client.chat.completions.create(
                model=self.chat_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": summary},
                ],
                temperature=0.9,
                max_tokens=50,
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI title extraction failed: {str(e)}")
            return {"title": "Untitled"}

    # def test(self):
    #     filter_str = self._build_filter(
    #         brand="Aperol", execution_level="Basic", placement="xx"
    #     )
    #     results = self.search_client.search(
    #         search_text="Do you have any Aperol promotional materials that can be placed on a counter or table inside the store?",
    #         # filter=filter_str,
    #         top=30,
    #         select=[
    #             "embedding",
    #             "id",
    #             "merged_content",
    #             "file_name",
    #             "page",
    #             "is_product_page",
    #             "product_brand",
    #             "product_execution_level",
    #             "product_placement",
    #             "product_type",
    #             "product_size",
    #             "product_PCSBU",
    #             "product_PCSSKU",
    #             "product_SKUBU",
    #             "product_image_url",
    #         ],
    #     )

    #     return results

    @timed_method
    def _extract_field(self, field_name: str, question: str) -> Optional[str]:
        try:
            logger.info(f"Extracting {field_name} from: {question}")
            mapping = self.VALUE_MAPPING.get(field_name, {})
            context_keywords = self.FIELD_CONTEXT.get(field_name, [])
            question_lower = question.lower()

            # 1. Directly match the complete value
            for value in set(mapping.values()):
                if re.search(rf"\b{re.escape(value.lower())}\b", question_lower):
                    logger.info(f"Direct match: {value}")
                    return value

            # 2. Matching mapping keywords
            for keyword, value in mapping.items():
                if re.search(rf"\b{re.escape(keyword)}\b", question_lower):
                    logger.info(f"Keyword match: {keyword} -> {value}")
                    return value

            # 3. Context Extraction
            has_context = any(
                re.search(rf"\b{re.escape(kw)}\b", question_lower)
                for kw in context_keywords
            )

            if has_context:
                # Try to extract the value after the context
                pattern = rf"\b({'|'.join(context_keywords)})\b\s*(?:is|of|for|:)?\s*['\"]?([\w\s]+)"
                match = re.search(pattern, question, re.IGNORECASE)
                if match and match.group(2):
                    extracted_value = match.group(2).strip()

                    # Try to match the mapping value
                    for keyword, value in mapping.items():
                        if keyword.lower() in extracted_value.lower():
                            return value

                    # Try to match the complete value
                    for value in set(mapping.values()):
                        if value.lower() in extracted_value.lower():
                            return value

                    # Return the original extracted value
                    return extracted_value

            logger.warn(f"No {field_name} found")
            return None
        except Exception as e:
            logger.error(f"Error extracting {field_name}: {str(e)}")
            return None

    @timed_method
    def _validate_and_classify_extraction(
        self, extraction: Dict[str, str]
    ) -> Dict[str, Any]:
        result = {"filters": {}, "keywords": {}}

        for key, value in extraction.items():
            if not isinstance(value, str):
                continue

            # Standardize field names
            clean_key = key.lower()
            mapped_key = self.FIELD_MAPPING.get(clean_key, clean_key)

            if mapped_key not in self.VALID_FIELDS:
                continue

            # Validate field values
            valid_value = self._validate_field_value(mapped_key, value)

            # Classification processing
            if mapped_key in self.FILTER_FIELDS:
                # Filter Fields
                final_value = valid_value if valid_value else value
                result["filters"][mapped_key] = final_value
                if not valid_value:
                    logger.warn(
                        f"Use original filter value: {mapped_key}='{value}' (unmapped)"
                    )
            else:
                # Keyword field
                result["keywords"][mapped_key] = value

        return result

    @timed_method
    def _validate_field_value(self, field: str, value: str) -> Optional[str]:
        if not value:
            return None

        mapping = self.VALUE_MAPPING.get(field, {})
        if not mapping:
            return value
        valid_values = set(mapping.values())
        value_lower = value.strip().lower()

        # Check if the value is already a standard value
        if value in valid_values:
            return value

        # Check if the lowercase version of the value is in the mapping
        if value_lower in mapping:
            return mapping[value_lower]

        # Check if a value partially matches a standard value
        for valid_value in valid_values:
            if valid_value.lower() in value_lower:
                return valid_value

        # Check if a value partially matches a map key
        for key, valid_value in mapping.items():
            if key in value_lower:
                return valid_value

        logger.warn(
            f"Invalid value for {field}: '{value}'. Valid values: {list(valid_values)}"
        )
        return None

    @timed_method
    def _merge_extractions(
        self, regex_result: Dict, ai_extraction: Dict
    ) -> Dict[str, Any]:
        final_filters = {}
        final_keywords = {}

        # Process regular extraction results
        self._merge_extraction_source(regex_result, final_filters, final_keywords)

        # Process AI extraction results
        self._merge_extraction_source(ai_extraction, final_filters, final_keywords)

        return {"filters": final_filters, "keywords": final_keywords}

    @timed_method
    def _merge_extraction_source(
        self, source: Dict, final_filters: Dict, final_keywords: Dict
    ):
        # Processing filter fields
        for key, value in source.get("filters", {}).items():
            if key in self.FILTER_FIELDS:
                valid_value = self._validate_field_value(key, value)
                final_value = valid_value if valid_value else value
                if key not in final_filters:
                    final_filters[key] = final_value
                if not valid_value:
                    logger.info(
                        f"To preserve unmapped filter values: {key}='{value}' (unmapped)"
                    )

        # Processing keyword fields
        for key, value in source.get("keywords", {}).items():
            if key in self.VALID_FIELDS:
                # Skip fields that already exist as filters
                if key in self.FILTER_FIELDS and key in final_filters:
                    continue
                if key not in final_keywords:
                    final_keywords[key] = value
