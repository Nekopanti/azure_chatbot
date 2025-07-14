import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from src.common.logger import get_logger

# Initialize logger
logger = get_logger("posm_service_azure")


class NaturalLanguageQASystem:
    def __init__(self, search_index_name: str):
        self.search_index_name = search_index_name
        self._init_openai_clients()
        self._init_search_client()
        self._init_field_mappings()
        self._init_value_mappings()

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

    def _init_search_client(self):
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=self.search_index_name,
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
        )

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

    def ask_question(self, question: str) -> Dict[str, Any]:
        try:
            logger.info(f"Processing question: {question}")

            extraction = self._extract_info(question)
            logger.info(f"Extraction results: {json.dumps(extraction, indent=2)}")

            context, relevant_docs = self._search_docs(
                question,
                extraction["filters"].get("product_brand"),
                extraction["filters"].get("product_execution_level"),
                extraction["filters"].get("product_placement"),
            )
            return self._generate_answer(question, context, relevant_docs, extraction)
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return {
                "answer": "Sorry, an error occurred while processing your question",
                "error": str(e),
                "sources": [],
            }

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

        return validated_regex

    def _extract_execution_level(self, question: str) -> Optional[str]:
        return self._extract_field("product_execution_level", question)

    def _extract_placement(self, question: str) -> Optional[str]:
        return self._extract_field("product_placement", question)

    def _extract_brand(self, question: str) -> Optional[str]:
        return self._extract_field("product_brand", question)

    def _extract_with_regex(self, question: str) -> Dict[str, str]:
        keywords = {}

        # Use unified extraction method
        if level := self._extract_execution_level(question):
            keywords["product_execution_level"] = level

        if placement := self._extract_placement(question):
            keywords["product_placement"] = placement

        if brand := self._extract_brand(question):
            keywords["product_brand"] = brand

        return keywords

    def _search_docs(
        self,
        question: str,
        brand: Optional[str],
        execution_level: Optional[str],
        placement: Optional[str],
    ) -> Tuple[str, List[Dict]]:
        try:
            # Perform a search to obtain candidate documents
            candidate_docs = self._get_candidate_docs(
                question, brand, execution_level, placement
            )
            # Calculate weighted scores and sort
            scored_docs = self._score_and_sort(candidate_docs)
            # Build return results
            return self._build_results(scored_docs)
        except Exception as e:
            logger.error(f"Search documents failed: {str(e)}")
            return "", []

    def _get_candidate_docs(
        self,
        question: str,
        brand: Optional[str],
        execution_level: Optional[str],
        placement: Optional[str],
    ) -> List[Dict]:
        filter_str = self._build_filter(brand, execution_level, placement)

        try:
            # semantic search
            results = self.search_client.search(
                search_text=question,
                query_type="semantic",
                semantic_configuration_name="default",
                filter=filter_str,
                top=10,
                select=[
                    "merged_content",
                    "product_summary",
                    "file_name",
                    "page",
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
            logger.error(f"Semantic search failed: {str(e)}")
            raise

        docs = []
        for result in results:
            doc = dict(result)
            doc["reranker_score"] = result.get("@search.reranker_score", 0)
            docs.append(doc)

        logger.info(f"Retrieved {len(docs)} candidate documents via semantic search")
        return docs

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

    def _score_and_sort(self, docs: List[Dict]) -> List[Dict]:
        if not docs:
            return []
        # Collect raw scores for normalization
        raw_scores = [doc.get("reranker_score", 0) for doc in docs]
        normalized_scores = [self._azure_normalize(score) for score in raw_scores]
        CONFIDENCE_MAPPING = {
            (0.9, 1.0): "Highly relevant",
            (0.7, 0.9): "Relevant but lacks detail",
            (0.5, 0.7): "Moderately related",
            (0.3, 0.5): "Partially relevant",
            (0.1, 0.3): "Slightly relevant",
            (0.0, 0.1): "Irrelevant",
        }

        # Assign normalized score and confidence label to each document
        for i, doc in enumerate(docs):
            doc["score"] = normalized_scores[i]
            doc["raw_score"] = raw_scores[i]
            for (min_val, max_val), label in CONFIDENCE_MAPPING.items():
                if min_val <= doc["score"] < max_val:
                    doc["confidence"] = label
                    break
            else:
                doc["confidence"] = "Irrelevant"

        sorted_docs = sorted(docs, key=lambda x: x["score"], reverse=True)

        # Dynamic threshold: the more documents, the higher the threshold
        min_threshold = self._calculate_threshold(normalized_scores, len(docs))
        filtered_docs = [doc for doc in sorted_docs if doc["score"] >= min_threshold][
            :10
        ]

        if filtered_docs:
            best_doc = filtered_docs[0]
            logger.info(
                f"Normalization results | "
                f"Raw scores: {min(raw_scores):.1f}-{max(raw_scores):.1f} | "
                f"Normalized: {min(normalized_scores):.2f}-{max(normalized_scores):.2f} | "
                f"Threshold: {min_threshold:.2f} | "
                f"Top confidence: {best_doc['confidence']} "
                f"(raw={best_doc['raw_score']:.2f}→norm={best_doc['score']:.2f}) | "
                f"Returned: {len(filtered_docs)} docs"
            )
        else:
            logger.info("No documents found above threshold")
        return filtered_docs

    def _build_results(self, docs: List[Dict]) -> Tuple[str, List[Dict]]:
        context_parts = []
        relevant_docs = []

        for doc in docs:
            context_parts.append(doc.get("merged_content", ""))
            relevant_docs.append(
                {
                    "product_summary": doc.get("product_summary", ""),
                    "brand": doc.get("product_brand", ""),
                    "execution_level": doc.get("product_execution_level", ""),
                    "placement": doc.get("product_placement", ""),
                    "file_name": doc.get("file_name", ""),
                    "page": doc.get("page", ""),
                    "product_type": doc.get("product_type", ""),
                    "branding": doc.get("product_branding", ""),
                    "Size": doc.get("product_size", ""),
                    "Type": doc.get("product_type", ""),
                    "PCSBU": doc.get("product_PCSBU", ""),
                    "PCSSKU": doc.get("product_PCSSKU", ""),
                    "SKUBU": doc.get("product_SKUBU", ""),
                    "image_url": doc.get("product_image_url", ""),
                    "score": doc.get("score", 0),
                }
            )

        return "\n\n".join(context_parts), relevant_docs

    def _generate_answer(
        self, question: str, context: str, relevant_docs: List[Dict], extraction: Dict
    ) -> Dict:
        prompt = self._build_prompt(question, relevant_docs)
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
            max_tokens=1024,
        )
        try:
            ai_response = json.loads(response.choices[0].message.content)
            if not self._validate_ai_response(ai_response):
                raise ValueError("Invalid response format from AI")
            response = self._build_final_response(ai_response, relevant_docs)
            return {
                "answer": response,
                "relevant_docs_count": len(relevant_docs),
            }
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an issue while processing your request. "
                "Please try rephrasing your question or contact support for assistance",
                "relevant_docs_count": 0,
            }

    def _build_prompt(self, question: str, relevant_docs: list) -> str:
        summaries = "\n".join(
            [
                f"Product {i+1}: {doc['product_summary']}"
                for i, doc in enumerate(relevant_docs)
            ]
        )
        count = len(relevant_docs)
        return f"""
        You are a product advisor helping users based on retrieved product summaries.

        ## User Question
        {question}

        ## Retrieved Product Summaries
        {summaries}

        ### Your task:
        - Begin with: "I found {count} products matching your criteria."
        - Highlight the best match (with brand, size, file name, and page if available)
        - End with a helpful phrase, e.g., "Let me know if you'd like more options."

        ### Response Format (STRICT JSON):
        {{
        "natural_language_response": "Your answer here (2-3 sentences)",
        "confidence": 0-100,
        "confidence_reason": "Brief justification"
        }}

        ### Example:
        {{
        "natural_language_response": "I found {count} Campari products matching your criteria. The best match is the Campari Lighthouse Stand, located on page 165 of the Global_POSM_Catalogue_24_25.pdf. It features Lighthouse execution level and measures 301.4 (L) x 1500.6 (H) mm with a depth of 302 mm. Let me know if you need further assistance!",
        "confidence": 95,
        "confidence_reason": "Strong match on brand, dimensions, and execution level."
        }}
        """

    def _validate_ai_response(self, response: Dict) -> bool:
        required_keys = ["natural_language_response", "confidence"]
        if not all(key in response for key in required_keys):
            logger.warn(f"Missing required keys: {required_keys}")
            return False
        return True

    def generate_title(self, summary: str) -> Dict[str, Any]:
        ai_title = self._title_with_ai(summary)
        return ai_title

    def _title_with_ai(self, summary: str, mode: str = "natural") -> Dict[str, Any]:
        try:
            if mode == "natural":
                system_prompt = """
                    You are an assistant that generates short and natural English titles for user queries.

                    Rules:
                    1. Title must be ≤ 3 words.
                    2. Make it natural, like a conversation or document title.
                    3. Preserve key information (e.g., brand, size, intent).
                    4. Avoid symbols or emojis.
                """
            else:
                system_prompt = """
                    You are an assistant that extracts and compresses key terms into a concise title.

                    Rules:
                    1. Title must be ≤ 3 words.
                    2. Focus on core keywords (brand, size, object).
                    3. Do not include filler words, personal pronouns, or emotion.
                    4. Use only English letters, numbers, or spaces.
                """

            response = self.chat_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": summary},
                ],
                temperature=0.5,
                max_tokens=20,
            )

            return {"title": response.choices[0].message.content}
        except Exception as e:
            logger.error(f"AI title extraction failed: {str(e)}")
            return {"title": "Untitled"}

    def _extract_field(self, field_name: str, question: str) -> Optional[str]:
        try:
            logger.info(f"Extracting {field_name} from: {question}")
            mapping = self.VALUE_MAPPING.get(field_name, {})
            context_keywords = self.FIELD_CONTEXT.get(field_name, [])
            question_lower = question.lower()

            # Directly match the complete value
            for value in set(mapping.values()):
                if re.search(rf"\b{re.escape(value.lower())}\b", question_lower):
                    logger.info(f"Direct match: {value}")
                    return value

            # Matching mapping keywords
            for keyword, value in mapping.items():
                if re.search(rf"\b{re.escape(keyword)}\b", question_lower):
                    logger.info(f"Keyword match: {keyword} -> {value}")
                    return value

            # Context Extraction
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
                pass

        return result

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

    def _azure_normalize(self, score: float) -> float:
        if score >= 4.0:
            return 1.0
        elif score >= 3.0:
            return 0.95 + min(0.05, (score - 3.0) * 0.1)
        elif score >= 2.5:
            return 0.85 + min(0.10, (score - 2.5) * 0.2)
        elif score >= 2.0:
            return 0.70 + min(0.15, (score - 2.0) * 0.3)
        elif score >= 1.0:
            return 0.40 + min(0.30, (score - 1.0) * 0.3)
        else:
            return max(0.0, min(0.4, score * 0.4))

    def _calculate_threshold(self, scores, n_docs):
        max_score = max(scores) if scores else 0.3
        if max_score >= 0.9:
            base = 0.7
        elif max_score >= 0.7:
            base = 0.5
        else:
            base = 0.3

        return min(0.9, max(0.2, base + 0.003 * n_docs))

    def _build_final_response(self, ai_response: dict, relevant_docs: list) -> dict:
        products = [
            {
                "Brand": doc.get("brand", "N/A"),
                "File": doc.get("file_name", "N/A"),
                "Page": doc.get("page", "N/A"),
                "Execution Level": doc.get("execution_level", "N/A"),
                "Placement": doc.get("placement", "N/A"),
                "Branding": doc.get("branding", "N/A"),
                "Size": doc.get("Size", "N/A"),
                "Type": doc.get("Type", "N/A"),
                "PCS/BU": doc.get("PCSBU", "N/A"),
                "PCS/SKU": doc.get("PCSSKU", "N/A"),
                "SKU/BU": doc.get("SKUBU", "N/A"),
                "image_url": doc.get("image_url", "N/A"),
                "product_summary": doc.get("product_summary", "N/A"),
                "match_score": f"{doc.get('score', 0):.2f}",
            }
            for doc in relevant_docs
        ]

        return {
            "natural_language_response": ai_response.get(
                "natural_language_response", ""
            ),
            "products": products,
            "confidence": ai_response.get("confidence", "N/A"),
            "confidence_reason": ai_response.get("confidence_reason", ""),
        }
