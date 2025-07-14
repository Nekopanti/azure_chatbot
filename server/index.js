const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
require("dotenv").config();
const { BlobServiceClient, generateBlobSASQueryParameters } = require("@azure/storage-blob");
const { env } = require("process");

const app = express();
const PORT = process.env.PORT || 3001;

// 解析存储账户名
function getStorageAccountName(connectionString) {
  const params = new URLSearchParams(connectionString.split(";").slice(1).join("&"));
  return params.get("AccountName");
}

// 从环境变量获取配置并校验
const connectionString = env.AZURE_CONNECTION_STRING;
const containerName = env.AZURE_CONTAINER_NAME;
const accountName = getStorageAccountName(connectionString);

if (!connectionString || !containerName || !accountName) {
  throw new Error("Missing Azure storage configuration in environment variables");
}

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static('public'))
app.use(bodyParser.urlencoded({ extended: true }));

let chatHistory = [];

app.get("/api/ask_question", async (req, res) => {
  try {
    // const { question } = req.body;
    // if (!question) {
    //   return res.status(400).json({ error: "Question is required" });
    // }

        // 这里直接返回提供的 JSON 数据
    const responseData ={"result":{
  "answer": {
            "natural_language_response": "I reviewed the available products and found 3 options that partially match your request for a size around 40x35 cm and SKU/BU of 10. None of the products fully meet the criteria, but they are close in size and other attributes. The most relevant product is an Aperol display rack with a size of 43x38 cm and a PCS/BU of 10, found on page 1 of sample1.pdf. The other two products have the same size but differ significantly in SKU/BU values. Let me know if you'd like more details or alternative recommendations.",
            "conclusion": "No perfect matches, but found 3 partially matching products.",
            "products": [
                {
                    "id": "test3",
                    "page": "3",
                    "brand": "Aperol",
                    "execution_level": "3",
                    "placement": "Top Shelf",
                    "source_file": "sample3.pdf",
                    "size": "43x38cm",
                    "type": "Display Rack",
                    "pcs_bu": "100",
                    "pcs_sku": "5555",
                    "sku_bu": "24545",
                    "image_sas_url": "https://posmpdfstorage.blob.core.windows.net/product-images/Global_POSM_Catalogue_24_25.pdf-22.jpg?sp=r&st=2025-06-25T03:48:44Z&se=2025-06-25T11:48:44Z&spr=https&sv=2024-11-04&sr=b&sig=9%2BEB7FKT6z4CYVMKnrGZX7C0V4Lcczo9BozTWPlEWDo%3D",
                    "is_product_page": true,
                    "product_summary": "This Aperol display rack has a size of 43x38 cm and is located on page 3 of sample3.pdf. While it matches the size criteria, its SKU/BU value is significantly higher than requested.",
                    "match_score": 0.65
                }
            ],
            "confidence": 85,
            "confidence_reason": "The products partially match the size criteria but differ in SKU/BU values. The closest match is Product 2, which aligns well with the PCS/BU requirement."
        },
        "relevant_docs_count": 3
}};

    res.json(responseData);

    // // 根据问题动态获取图片文件名
    // const blobName = getImageFileName(question);
    // if (!blobName) {
    //   return res.json({ answer: "No image found for this question", imageUrl: null });
    // }

    // // 生成 SAS 令牌
    // const sasToken = generateSAS(blobName);
    
    // // 构建带 SAS 的 URL
    // const imageUrl = `https://${accountName}.blob.core.windows.net/${containerName}/${blobName}?${sasToken}`;
    
    // // 生成回答
    // const reply = generateMockAnswer(question);
    
    // // 保存聊天记录
    // chatHistory.push({ question, answer: reply, imageUrl });
    
    // res.json({ answer: reply, imageUrl, chatHistory });
  } catch (error) {
    console.error("Error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/generate_title", async (req, res) => {
  res.json({title:{title: "Aperol Display Stand2"}})
});

// 根据问题匹配图片文件名（示例逻辑）
function getImageFileName(question) {
  return "POSM_TEST/test.png"; // 默认图片
}

// 生成模拟回答
function generateMockAnswer(question) {
  return `You asked: "${question}"`;
}

// 生成 SAS 令牌
function generateSAS(blobName, expiresInMinutes = 60) {
  const blobServiceClient = BlobServiceClient.fromConnectionString(connectionString);
  const containerClient = blobServiceClient.getContainerClient(containerName);
  const credential = containerClient.credential; // 获取凭证

  const sasOptions = {
    containerName,
    blobName,
    permissions: "r", // 只读权限
    startsOn: new Date(),
    expiresOn: new Date(new Date().getTime() + expiresInMinutes * 60 * 1000 * 24),
  };

  const sasToken = generateBlobSASQueryParameters(sasOptions, credential).toString();
  return sasToken;
}

app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`Azure Container: ${containerName}`);
});