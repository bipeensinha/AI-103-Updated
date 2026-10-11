# ============================================================
# AI IMAGE GENERATOR STUDIO
# GPT-image-2 + Microsoft Foundry
# ============================================================

import os
import base64

from dotenv import load_dotenv

from fastapi import FastAPI, Form, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from openai import AzureOpenAI


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT"
)

AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY"
)

AZURE_OPENAI_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT"
)

AZURE_OPENAI_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION",
    "2025-04-01-preview"
)


# ============================================================
# 2. VALIDATE CONFIGURATION
# ============================================================

if not AZURE_OPENAI_ENDPOINT:

    raise ValueError(
        "AZURE_OPENAI_ENDPOINT is missing from .env"
    )


if not AZURE_OPENAI_API_KEY:

    raise ValueError(
        "AZURE_OPENAI_API_KEY is missing from .env"
    )


if not AZURE_OPENAI_DEPLOYMENT:

    raise ValueError(
        "AZURE_OPENAI_DEPLOYMENT is missing from .env"
    )


# ============================================================
# 3. CREATE CLIENT
# ============================================================

client = AzureOpenAI(

    api_key=AZURE_OPENAI_API_KEY,

    azure_endpoint=AZURE_OPENAI_ENDPOINT,

    api_version=AZURE_OPENAI_API_VERSION

)


# ============================================================
# 4. FASTAPI
# ============================================================

app = FastAPI(

    title="AI Image Generator Studio",

    description=(
        "GPT-image-2 image generation application "
        "powered by Microsoft Foundry."
    ),

    version="1.0.0"

)


# ============================================================
# 5. CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# ============================================================
# 6. ROOT
# ============================================================

@app.get("/")
async def root():

    return {

        "application":
            "AI Image Generator Studio",

        "status":
            "running",

        "model":
            AZURE_OPENAI_DEPLOYMENT,

        "message":
            "GPT-image-2 is ready."

    }


# ============================================================
# 7. HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {

        "status": "healthy",

        "model":
            AZURE_OPENAI_DEPLOYMENT

    }


# ============================================================
# 8. IMAGE GENERATION
# ============================================================

@app.post("/generate")
async def generate_image(

    prompt: str = Form(...),

    size: str = Form("1024x1024"),

    quality: str = Form("high"),

    n: int = Form(1)

):

    # --------------------------------------------------------
    # Validate prompt
    # --------------------------------------------------------

    if not prompt.strip():

        raise HTTPException(

            status_code=400,

            detail="Prompt cannot be empty."

        )


    # --------------------------------------------------------
    # Validate size
    # --------------------------------------------------------

    allowed_sizes = [

        "1024x1024",

        "1536x1024",

        "1024x1536"

    ]

    if size not in allowed_sizes:

        raise HTTPException(

            status_code=400,

            detail=(
                f"Unsupported size: {size}. "
                f"Use one of: {allowed_sizes}"
            )

        )


    # --------------------------------------------------------
    # Validate quality
    # --------------------------------------------------------

    allowed_quality = [

        "low",

        "medium",

        "high",

        "auto"

    ]

    if quality not in allowed_quality:

        raise HTTPException(

            status_code=400,

            detail=(
                f"Unsupported quality: {quality}. "
                f"Use one of: {allowed_quality}"
            )

        )


    # --------------------------------------------------------
    # Generate image
    # --------------------------------------------------------

    try:

        result = client.images.generate(

            model=AZURE_OPENAI_DEPLOYMENT,

            prompt=prompt,

            n=n,

            size=size,

            quality=quality

        )

    except Exception as e:

        print(
            "GPT-image-2 ERROR:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                f"Azure OpenAI error: {str(e)}"
            )

        )


    # --------------------------------------------------------
    # Get generated images
    # --------------------------------------------------------

    images = []


    for item in result.data:

        # GPT image models commonly return
        # base64 encoded image data.

        if hasattr(item, "b64_json") and item.b64_json:

            images.append({

                "type": "base64",

                "data":
                    item.b64_json

            })


        elif hasattr(item, "url") and item.url:

            images.append({

                "type": "url",

                "url":
                    item.url

            })


    # --------------------------------------------------------
    # Check result
    # --------------------------------------------------------

    if not images:

        raise HTTPException(

            status_code=500,

            detail=(
                "Image generation completed, "
                "but no image data was returned."
            )

        )


    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        "success": True,

        "model":
            AZURE_OPENAI_DEPLOYMENT,

        "prompt":
            prompt,

        "size":
            size,

        "quality":
            quality,

        "images":
            images

    }


# ============================================================
# 9. RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "main:app",

        host="0.0.0.0",

        port=8001,

        reload=True

    )