import os
import json
import base64
import requests
from pdf2image import convert_from_path
from io import BytesIO
from pathlib import Path

SERVER_URL = "http://localhost:8080/v1/chat/completions"


def process_image_to_b64(pil_img):
    buffered = BytesIO()
    pil_img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def analyze_and_extract(pil_img):
    """Sender billede til Qwen3-VL for både rotationstjek og OCR"""
    b64_img = process_image_to_b64(pil_img)

    prompt = """Analyze this image and perform two tasks:
1. Determine the rotation angle (0, 90, 180, or 270) needed to make the text upright for reading.
2. Extract all text from the image accurately.

Return ONLY a JSON object with these keys:
- "rotation_needed": (int)
- "extracted_values": (string)"""

    prompt1 = """Analyze this image and perform two tasks:
1. Determine the rotation angle (0, 90, 180, or 270) needed to make the text upright for reading.
2. Extract values from the table in the image with column headers: "DATO", "POSTERINGSTEKST", "AFSENDER INFO", "BELØB", "OPRINDELIGT BELØB" and "SALDO"
Return ONLY a JSON object with these keys:
- "rotation_needed": (int)
- "extracted_values": (array of array of strings)"""

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                    },
                ],
            }
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},  # Hvis din server understøtter det
    }

    try:
        response = requests.post(SERVER_URL, json=payload, timeout=120)
        # Rens output for evt. markdown (```json ... ```)
        print(response.json())
        raw_content = response.json()["choices"][0]["message"]["content"]
        clean_content = raw_content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_content)
    except Exception as e:
        print(f"Fejl ved API-kald: {e}")
        return None


def extract_fields(ocr_text):
    prompt = f"""Her er tekst fra en faktura:
    {ocr_text}
    
    Returnér KUN følgende som JSON:
    - firmanavn
    - total_pris
    - momspligtigt beløb
    - momsbeløb
    - faktureringsdato
    """

    # Send til din anden server på port 8081
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,  # Vi vil have fakta, ikke kreativitet
    }

    response = requests.post("http://localhost:8081/v1/chat/completions", json=payload)
    return response.json()["choices"][0]["message"]["content"]


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
        if not filename.startswith("p"):
            continue
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
            img_result = analyze_and_extract(img)
            if img_result:
                angle = img_result.get("rotation_needed", 0)
                extracted_values = img_result.get("extracted_values", "")
                print(angle)
                print(extracted_values)
                result = extract_fields(extracted_values)
                # Gem resultatet
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"Færdig! Gemt i {output_path}")
        break


if __name__ == "__main__":
    run_batch()
