const API_URL = "http://localhost:8001";

const prompt = document.getElementById("prompt");
const charCount = document.getElementById("charCount");
const generateBtn = document.getElementById("generateBtn");
const resultImage = document.getElementById("resultImage");
const loading = document.getElementById("loading");
const generationStatus = document.getElementById("generationStatus");
const downloadBtn = document.getElementById("downloadBtn");
const errorBox = document.getElementById("errorBox");
const toast = document.getElementById("toast");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function updateCount() {
  charCount.textContent = `${prompt.value.length}/4000`;
}
prompt.addEventListener("input", updateCount);
updateCount();

document.getElementById("advancedBtn").addEventListener("click", () => {
  document.getElementById("advancedPanel").classList.toggle("hidden");
});

document.querySelectorAll(".prompt-card").forEach(card => {
  card.addEventListener("click", () => {
    prompt.value = card.dataset.prompt;
    updateCount();
    document.getElementById("generate").scrollIntoView({behavior:"smooth", block:"start"});
    showToast("Prompt added");
  });
});

const surprises = [
  "A futuristic smart city in Bangalore in 2050, cinematic photography, golden hour, ultra detailed",
  "A professional AI conference in Mumbai, premium corporate poster, futuristic technology, photorealistic",
  "A luxury eco-resort in the Himalayas, sunrise, architectural photography, cinematic",
  "A humanoid AI assistant helping students in a modern classroom, realistic, inspirational",
  "A futuristic Indian space station above Earth, cinematic lighting, highly detailed"
];

document.getElementById("surpriseBtn").addEventListener("click", () => {
  prompt.value = surprises[Math.floor(Math.random() * surprises.length)];
  updateCount();
  showToast("Surprise prompt generated");
});

document.querySelectorAll(".style-preset").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".style-preset").forEach(x => x.classList.remove("selected"));
    btn.classList.add("selected");
    const style = btn.textContent.trim();
    document.getElementById("style").value = style;
    showToast(`${style} selected`);
  });
});

document.querySelectorAll(".side-tool").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".side-tool").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    if (btn.dataset.tool !== "Text to Image") {
      showToast(`${btn.dataset.tool} UI selected — connect this tool to your backend when ready`);
    }
  });
});

async function generateImage() {
  const text = prompt.value.trim();
  if (!text) {
    showToast("Please enter a prompt");
    prompt.focus();
    return;
  }

  errorBox.classList.add("hidden");
  loading.classList.remove("hidden");
  generateBtn.disabled = true;
  generateBtn.textContent = "✣ Generating...";
  generationStatus.textContent = "Generating with GPT-image-2...";
  downloadBtn.disabled = true;

  try {
    const form = new FormData();
    form.append("prompt", text);
    form.append("size", document.getElementById("size").value);
    form.append("quality", document.getElementById("quality").value);
    form.append("n", document.getElementById("count").value);

    const response = await fetch(`${API_URL}/generate`, {
      method: "POST",
      body: form
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.detail || data.error || "Image generation failed.");
    }

    if (!data.images || !data.images.length) {
      throw new Error("The API returned no images.");
    }

    const first = data.images[0];
    const src = first.b64_json
      ? `data:image/png;base64,${first.b64_json}`
      : first.url;

    resultImage.src = src;
    resultImage.dataset.downloadUrl = src;
    downloadBtn.disabled = false;
    generationStatus.textContent = "Image generated successfully";
    showToast("Your image is ready!");
  } catch (err) {
    console.error(err);
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
    generationStatus.textContent = "Generation failed";
  } finally {
    loading.classList.add("hidden");
    generateBtn.disabled = false;
    generateBtn.textContent = "✣ Generate Image";
  }
}

generateBtn.addEventListener("click", generateImage);

downloadBtn.addEventListener("click", async () => {
  const url = resultImage.dataset.downloadUrl || resultImage.src;
  if (!url) return;

  try {
    if (url.startsWith("data:")) {
      const a = document.createElement("a");
      a.href = url;
      a.download = `ai-image-${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } else {
      const res = await fetch(url);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `ai-image-${Date.now()}.png`;
      a.click();
      URL.revokeObjectURL(blobUrl);
    }
    showToast("Download started");
  } catch {
    window.open(url, "_blank");
  }
});

document.querySelectorAll(".thumb").forEach(thumb => {
  thumb.addEventListener("click", () => {
    document.querySelectorAll(".thumb").forEach(x => x.classList.remove("active"));
    thumb.classList.add("active");
    const img = thumb.querySelector("img");
    if (img) resultImage.src = img.src;
  });
});

document.querySelectorAll(".billing").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".billing").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    const period = btn.dataset.period;
    document.querySelectorAll(".price[data-monthly]").forEach(price => {
      price.firstChild.textContent = price.dataset[period];
    });
  });
});

document.querySelectorAll(".price-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const plan = btn.dataset.plan;
    if (plan === "Free") {
      showToast("Free plan selected — connect your signup flow here.");
    } else if (plan === "Enterprise") {
      showToast("Contact Sales selected — connect your sales form here.");
    } else {
      showToast(`${plan} plan selected — connect Stripe/Razorpay checkout here.`);
    }
  });
});

// Smooth navigation and initial health check.
async function checkBackend() {
  try {
    const r = await fetch(`${API_URL}/health`);
    if (r.ok) {
      generationStatus.textContent = "Backend online • Ready to create";
    }
  } catch {
    generationStatus.textContent = "Demo preview • Backend not connected";
  }
}
checkBackend();
