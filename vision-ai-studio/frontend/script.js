// =====================================================
// CONFIGURATION
// =====================================================

const API_URL = "http://localhost:8000";


// =====================================================
// DOM ELEMENTS
// =====================================================

const imageInput = document.getElementById("imageInput");

const browseButton = document.getElementById("browseButton");

const dropZone = document.getElementById("dropZone");

const imagePreview = document.getElementById("imagePreview");

const uploadPlaceholder =
    document.getElementById("uploadPlaceholder");

const question =
    document.getElementById("question");

const analyzeButton =
    document.getElementById("analyzeButton");

const result =
    document.getElementById("result");

const answer =
    document.getElementById("answer");

const emptyResult =
    document.getElementById("emptyResult");

const loading =
    document.getElementById("loading");

const analysisStatus =
    document.getElementById("analysisStatus");

const selectedUseCase =
    document.getElementById("selectedUseCase");


// =====================================================
// APPLICATION STATE
// =====================================================

let selectedFile = null;

let selectedUseCaseValue = "vehicle";


// =====================================================
// USE CASE NAMES
// =====================================================

const useCaseNames = {

    vehicle: "Vehicle Inspection",

    interior: "Interior Designer",

    fashion: "Fashion Stylist",

    hotel: "Hotel Concierge",

    food: "Food Assistant",

    document: "Document Analyzer"

};


// =====================================================
// DEFAULT QUESTIONS
// =====================================================

const defaultQuestions = {

    vehicle:
        "What damage can you see in this vehicle image?",

    interior:
        "How can I improve the design of this room?",

    fashion:
        "Analyze this outfit and suggest improvements.",

    hotel:
        "What useful information can you identify in this image?",

    food:
        "What food or menu items can you identify?",

    document:
        "Extract and summarize the important information in this document."

};


// =====================================================
// FILE SELECTION
// =====================================================

browseButton.addEventListener(
    "click",
    () => {

        imageInput.click();

    }
);


dropZone.addEventListener(
    "click",
    () => {

        imageInput.click();

    }
);


imageInput.addEventListener(
    "change",
    (event) => {

        const file = event.target.files[0];

        if (file) {

            loadImage(file);

        }

    }
);


// =====================================================
// DRAG AND DROP
// =====================================================

dropZone.addEventListener(
    "dragover",
    (event) => {

        event.preventDefault();

        dropZone.style.borderColor = "#635bff";

    }
);


dropZone.addEventListener(
    "dragleave",
    () => {

        dropZone.style.borderColor = "";

    }
);


dropZone.addEventListener(
    "drop",
    (event) => {

        event.preventDefault();

        dropZone.style.borderColor = "";

        const file = event.dataTransfer.files[0];

        if (file) {

            loadImage(file);

        }

    }
);


// =====================================================
// LOAD IMAGE
// =====================================================

function loadImage(file) {

    if (!file.type.startsWith("image/")) {

        alert("Please select an image file.");

        return;

    }

    selectedFile = file;

    const reader = new FileReader();

    reader.onload = function(event) {

        imagePreview.src = event.target.result;

        imagePreview.style.display = "block";

        uploadPlaceholder.style.display = "none";

    };

    reader.readAsDataURL(file);

    analysisStatus.textContent = "Image Ready";

}


// =====================================================
// USE CASE SELECTION
// =====================================================

document
    .querySelectorAll(".use-case")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                // Remove active state

                document
                    .querySelectorAll(".use-case")
                    .forEach(item => {

                        item.classList.remove("active");

                    });


                // Add active state

                button.classList.add("active");


                // Save selected use case

                selectedUseCaseValue =
                    button.dataset.usecase;


                // Update heading

                selectedUseCase.textContent =
                    useCaseNames[selectedUseCaseValue];


                // Update suggested question

                question.value =
                    defaultQuestions[selectedUseCaseValue];

            }
        );

    });


// =====================================================
// PROMPT SUGGESTIONS
// =====================================================

document
    .querySelectorAll(".prompt-suggestions button")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                question.value =
                    button.dataset.question;

            }
        );

    });


// =====================================================
// ANALYZE IMAGE
// =====================================================

analyzeButton.addEventListener(
    "click",
    analyzeImage
);


async function analyzeImage() {

    // -------------------------------------------------
    // Validate image
    // -------------------------------------------------

    if (!selectedFile) {

        alert("Please upload an image first.");

        return;

    }


    // -------------------------------------------------
    // Validate question
    // -------------------------------------------------

    if (!question.value.trim()) {

        alert("Please enter a question.");

        question.focus();

        return;

    }


    // -------------------------------------------------
    // UI - Loading
    // -------------------------------------------------

    emptyResult.classList.add("hidden");

    result.classList.add("hidden");

    loading.classList.remove("hidden");

    analysisStatus.textContent =
        "Analyzing...";

    analyzeButton.disabled = true;

    analyzeButton.innerHTML =
        "⏳ Analyzing with GPT-5.1...";


    // -------------------------------------------------
    // Create FormData
    // -------------------------------------------------

    const formData = new FormData();

    formData.append(
        "image",
        selectedFile
    );

    formData.append(
        "question",
        question.value
    );

    formData.append(
        "use_case",
        selectedUseCaseValue
    );


    try {

        // -------------------------------------------------
        // Call FastAPI
        // -------------------------------------------------

        const response =
            await fetch(
                `${API_URL}/analyze`,
                {
                    method: "POST",

                    body: formData
                }
            );


        // -------------------------------------------------
        // Check HTTP response
        // -------------------------------------------------

        if (!response.ok) {

            const errorData =
                await response.json();

            throw new Error(
                errorData.detail ||
                "API request failed."
            );

        }


        // -------------------------------------------------
        // Read response
        // -------------------------------------------------

        const data =
            await response.json();


        // -------------------------------------------------
        // Display response
        // -------------------------------------------------

        answer.textContent =
            data.answer;


        selectedUseCase.textContent =
            useCaseNames[
                data.use_case
            ] || data.use_case;


        // -------------------------------------------------
        // Show result
        // -------------------------------------------------

        loading.classList.add("hidden");

        result.classList.remove("hidden");

        analysisStatus.textContent =
            "Analysis Complete";


    }
    catch (error) {

        console.error(error);


        loading.classList.add("hidden");


        analysisStatus.textContent =
            "Error";


        emptyResult.classList.remove("hidden");


        alert(
            "Something went wrong:\n\n" +
            error.message
        );

    }
    finally {

        analyzeButton.disabled = false;

        analyzeButton.innerHTML =
            "<span>✦</span> Analyze with GPT-5.1";

    }

}


// =====================================================
// INITIALIZE
// =====================================================

question.value =
    defaultQuestions.vehicle;

selectedUseCase.textContent =
    useCaseNames.vehicle;