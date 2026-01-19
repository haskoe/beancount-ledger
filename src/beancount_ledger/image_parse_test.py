import os
import base64
import requests
from pdf2image import convert_from_path
from io import BytesIO
from pathlib import Path

SERVER_URL = "http://localhost:8080/v1/chat/completions"


def process_image(image):
    """Konverterer et PIL-billede til base64-streng"""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def get_text_from_ai(base64_image):
    """Sender billede til llama-server og returnerer teksten"""
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all text from this image accurately. Use markdown format.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "temperature": 0.2,  # Lav temperatur = mere præcis OCR
        "stream": False,
    }

    try:
        response = requests.post(SERVER_URL, json=payload, timeout=120)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"FEJL under AI-behandling: {e}"


def handle_image_test(ctx):
    files = [
        f
        for f in os.listdir(ctx.indbakke_dir)
        if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))
    ]

    if not files:
        print("Ingen filer fundet i input-mappen.")
        return

    for filename in files:
        print(f"\nBehandler: {filename}...")
        file_path = os.path.join(ctx.indbakke_dir, filename)
        output_path = os.path.join(ctx.indbakke_dir, f"{filename}.txt")

        extracted_text = ""

        # Håndter PDF
        if filename.lower().endswith(".pdf"):
            pages = convert_from_path(file_path, 300)
            for i, page in enumerate(pages):
                print(f"  - Side {i + 1} af {len(pages)}")
                b64_img = process_image(page)
                extracted_text += f"\n--- SIDE {i + 1} ---\n" + get_text_from_ai(
                    b64_img
                )

        # Håndter Billeder
        else:
            from PIL import Image

            img = Image.open(file_path)
            extracted_text = get_text_from_ai(process_image(img))

        # Gem resultatet
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        print(f"Færdig! Gemt i {output_path}")


if __name__ == "__main__":
    run_batch()
