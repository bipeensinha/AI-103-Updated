# ============================================================
# Vision AI Studio
# GPT-5.1 Vision Application
#
# Backend:
#   Python
#   FastAPI
#   Azure OpenAI / Microsoft Foundry
#
# ============================================================

import os
import base64

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    File,
    Form,
    UploadFile,
    HTTPException
)

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
        "AZURE_OPENAI_ENDPOINT is not configured in .env"
    )


if not AZURE_OPENAI_API_KEY:

    raise ValueError(
        "AZURE_OPENAI_API_KEY is not configured in .env"
    )


if not AZURE_OPENAI_DEPLOYMENT:

    raise ValueError(
        "AZURE_OPENAI_DEPLOYMENT is not configured in .env"
    )


# ============================================================
# 3. CREATE AZURE OPENAI CLIENT
# ============================================================

client = AzureOpenAI(

    api_key=AZURE_OPENAI_API_KEY,

    azure_endpoint=AZURE_OPENAI_ENDPOINT,

    api_version=AZURE_OPENAI_API_VERSION

)


# ============================================================
# 4. CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="Vision AI Studio",

    description="""
    Vision AI Studio is a multimodal AI application
    powered by GPT-5.1 through Microsoft Foundry.

    Users can upload images and ask questions about
    the visual content.
    """,

    version="1.0.0"

)


# ============================================================
# 5. ENABLE CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# ============================================================
# 6. ALLOWED IMAGE TYPES
# ============================================================

ALLOWED_IMAGE_TYPES = [

    "image/jpeg",

    "image/png",

    "image/webp",

    "image/gif"

]


# ============================================================
# 7. SYSTEM PROMPTS
# ============================================================

SYSTEM_PROMPTS = {


    # --------------------------------------------------------
    # VEHICLE
    # --------------------------------------------------------

    "vehicle": """

You are Vision AI Studio's Vehicle Inspection Assistant.

Analyze the uploaded vehicle image carefully.

Identify:

1. Vehicle type if visible
2. Visible damage
3. Damaged components
4. Scratches
5. Dents
6. Cracks
7. Paint damage
8. Possible severity
9. Potential visible safety concerns
10. Recommended next inspection or action

Important rules:

- Only describe what can reasonably be observed.
- Do not claim hidden mechanical or structural damage.
- Clearly distinguish visible observations from assumptions.
- Recommend professional inspection when appropriate.
- Do not provide a definitive insurance or repair cost.
- Be concise and professional.

Structure your response using:

OBSERVATIONS

DAMAGE

SEVERITY

POSSIBLE CONCERNS

RECOMMENDED ACTION
""",


    # --------------------------------------------------------
    # INTERIOR DESIGNER
    # --------------------------------------------------------

    "interior": """

You are Vision AI Studio's AI Interior Designer.

Analyze the uploaded room/interior image.

Identify:

1. Room type
2. Furniture
3. Color palette
4. Lighting
5. Flooring
6. Walls
7. Layout
8. Available space
9. Design style

Provide practical recommendations for improving the room.

Consider:

- Modern design
- Luxury design
- Space optimization
- Lighting
- Colors
- Furniture placement
- Decorative elements

Do not invent objects that are not visible.

Structure your response using:

ROOM ANALYSIS

CURRENT STYLE

WHAT WORKS

IMPROVEMENT IDEAS

RECOMMENDED STYLE
""",


    # --------------------------------------------------------
    # FASHION
    # --------------------------------------------------------

    "fashion": """

You are Vision AI Studio's AI Fashion Stylist.

Analyze the uploaded image.

Identify visible:

1. Clothing
2. Colors
3. Patterns
4. Footwear
5. Accessories
6. Overall style
7. Apparent occasion

Provide practical styling recommendations.

You may suggest:

- Color combinations
- Accessories
- Footwear
- Layering
- Alternative styling
- Occasion suitability

Only comment on visible clothing.

Do not make assumptions about the person's identity.

Structure your response using:

OUTFIT ANALYSIS

STYLE

COLOR ANALYSIS

WHAT WORKS

RECOMMENDATIONS
""",


    # --------------------------------------------------------
    # HOTEL
    # --------------------------------------------------------

    "hotel": """

You are Vision AI Studio's AI Hotel Concierge.

Analyze the uploaded image.

The image may contain:

- Hotel facilities
- Restaurant menus
- Hotel rooms
- Signs
- Food
- Amenities
- Directions
- Services

Extract useful information from the image.

If the image contains a menu:

- Identify dishes
- Identify categories
- Identify prices when clearly visible
- Identify vegetarian indicators when explicitly shown

Do not invent information that cannot be read or observed.

Clearly state when information is uncertain.
""",


    # --------------------------------------------------------
    # FOOD
    # --------------------------------------------------------

    "food": """

You are Vision AI Studio's Food Assistant.

Analyze the uploaded food or menu image.

Identify:

1. Food items
2. Menu categories
3. Ingredients when reasonably identifiable
4. Prices if visible
5. Vegetarian indicators when explicitly shown
6. Non-vegetarian indicators when explicitly shown

Provide useful recommendations based on the user's question.

Important:

- Do not claim allergy safety from an image alone.
- Do not invent ingredients.
- If ingredients are uncertain, clearly say so.
- Clearly distinguish what is visible from what is inferred.
""",


    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    "document": """

You are Vision AI Studio's Document Analysis Assistant.

Analyze the uploaded document image.

Extract and explain:

1. Visible text
2. Headings
3. Tables
4. Important information
5. Dates
6. Numbers
7. Key observations
8. Actions or recommendations when requested

Preserve the meaning of the original document.

If text is unclear or unreadable:

- Clearly say that it is unclear.
- Do not invent the missing text.

Provide a concise summary first,
followed by important details.
"""

}


# ============================================================
# 8. DEFAULT SYSTEM PROMPT
# ============================================================

DEFAULT_SYSTEM_PROMPT = """

You are Vision AI Studio.

You are a multimodal AI assistant powered by GPT-5.1.

You can analyze images and answer questions about
their visual content.

Your responsibilities include:

- Understanding uploaded images
- Identifying visible objects
- Reading visible text
- Understanding visual context
- Answering questions
- Reasoning about visible information
- Providing useful recommendations
- Communicating uncertainty clearly

Important:

Never invent information that cannot reasonably
be determined from the image.

Clearly distinguish:

OBSERVED INFORMATION

from

INFERRED INFORMATION.

When the image is insufficient to answer a question,
say so.
"""


# ============================================================
# 9. ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {

        "application": "Vision AI Studio",

        "status": "running",

        "model": AZURE_OPENAI_DEPLOYMENT,

        "message":
            "GPT-5.1 Vision API is ready."

    }


# ============================================================
# 10. HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {

        "status": "healthy",

        "application": "Vision AI Studio",

        "model": AZURE_OPENAI_DEPLOYMENT

    }


# ============================================================
# 11. GET AVAILABLE USE CASES
# ============================================================

@app.get("/use-cases")
async def get_use_cases():

    return {

        "use_cases": [

            {
                "id": "vehicle",
                "name": "Vehicle Inspection",
                "icon": "🚗"
            },

            {
                "id": "interior",
                "name": "Interior Designer",
                "icon": "🏠"
            },

            {
                "id": "fashion",
                "name": "Fashion Stylist",
                "icon": "👔"
            },

            {
                "id": "hotel",
                "name": "Hotel Concierge",
                "icon": "🏨"
            },

            {
                "id": "food",
                "name": "Food Assistant",
                "icon": "🍽️"
            },

            {
                "id": "document",
                "name": "Document Analyzer",
                "icon": "📄"
            }

        ]

    }


# ============================================================
# 12. IMAGE ANALYSIS ENDPOINT
# ============================================================

@app.post("/analyze")
async def analyze_image(

    image: UploadFile = File(...),

    question: str = Form(
        "What do you see in this image?"
    ),

    use_case: str = Form("general")

):

    # ========================================================
    # Validate image content type
    # ========================================================

    if not image.content_type:

        raise HTTPException(

            status_code=400,

            detail="Unable to determine image type."

        )


    if image.content_type not in ALLOWED_IMAGE_TYPES:

        raise HTTPException(

            status_code=400,

            detail=(
                f"Unsupported image type: "
                f"{image.content_type}. "
                f"Supported types: JPG, PNG, WEBP, GIF."
            )

        )


    # ========================================================
    # Read image
    # ========================================================

    try:

        image_bytes = await image.read()

    except Exception as e:

        raise HTTPException(

            status_code=400,

            detail=f"Unable to read uploaded image: {str(e)}"

        )


    # ========================================================
    # Validate image
    # ========================================================

    if not image_bytes:

        raise HTTPException(

            status_code=400,

            detail="Uploaded image is empty."

        )


    # ========================================================
    # Convert image to Base64
    # ========================================================

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # ========================================================
    # Select system prompt
    # ========================================================

    system_prompt = SYSTEM_PROMPTS.get(

        use_case.lower(),

        DEFAULT_SYSTEM_PROMPT

    )


    # ========================================================
    # Create image Data URL
    # ========================================================

    image_data_url = (

        f"data:{image.content_type};base64,"
        f"{encoded_image}"

    )


    # ========================================================
    # Call GPT-5.1
    # ========================================================

    try:

        response = client.chat.completions.create(

            model=AZURE_OPENAI_DEPLOYMENT,

            messages=[

                {
                    "role": "system",

                    "content": system_prompt
                },

                {

                    "role": "user",

                    "content": [

                        {

                            "type": "text",

                            "text": question

                        },

                        {

                            "type": "image_url",

                            "image_url": {

                                "url": image_data_url

                            }

                        }

                    ]

                }

            ],

            # IMPORTANT:
            # GPT-5.1 does not support max_tokens.
            # Use max_completion_tokens instead.

            max_completion_tokens=1200

        )


    except Exception as e:

        print(
            "Azure OpenAI Error:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                f"Azure OpenAI error: {str(e)}"
            )

        )


    # ========================================================
    # Extract response
    # ========================================================

    try:

        answer = response.choices[
            0
        ].message.content

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=(
                "Unable to extract model response: "
                f"{str(e)}"
            )

        )


    # ========================================================
    # Return response
    # ========================================================

    return {

        "success": True,

        "application": "Vision AI Studio",

        "use_case": use_case,

        "filename": image.filename,

        "content_type": image.content_type,

        "question": question,

        "answer": answer,

        "model": AZURE_OPENAI_DEPLOYMENT

    }


# ============================================================
# 13. TEXT CHAT ENDPOINT
# ============================================================

@app.post("/chat")
async def chat(

    question: str = Form(...)

):

    if not question.strip():

        raise HTTPException(

            status_code=400,

            detail="Question cannot be empty."

        )


    try:

        response = client.chat.completions.create(

            model=AZURE_OPENAI_DEPLOYMENT,

            messages=[

                {

                    "role": "system",

                    "content":
                        DEFAULT_SYSTEM_PROMPT

                },

                {

                    "role": "user",

                    "content": question

                }

            ],

            # IMPORTANT:
            # GPT-5.1 uses max_completion_tokens.

            max_completion_tokens=1000

        )


    except Exception as e:

        print(
            "Azure OpenAI Error:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                f"Azure OpenAI error: {str(e)}"
            )

        )


    return {

        "success": True,

        "question": question,

        "answer":
            response.choices[0].message.content,

        "model":
            AZURE_OPENAI_DEPLOYMENT

    }


# ============================================================
# 14. APPLICATION STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
async def startup_event():

    print("")
    print("=" * 60)
    print("       VISION AI STUDIO")
    print("=" * 60)

    print(
        f"Deployment : {AZURE_OPENAI_DEPLOYMENT}"
    )

    print(
        f"API Version: {AZURE_OPENAI_API_VERSION}"
    )

    print(
        "Status     : Ready"
    )

    print("=" * 60)
    print("")


# ============================================================
# 15. RUN APPLICATION DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "main:app",

        host="0.0.0.0",

        port=8000,

        reload=True

    )