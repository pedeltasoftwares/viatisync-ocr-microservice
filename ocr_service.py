import fitz
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image
import dateparser
import re
from io import BytesIO
import cv2

# Inicializar OCR una sola vez
ocr = PaddleOCR(lang='es', use_angle_cls=True)

def pdf_to_image_bytes(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    img_data = pix.tobytes("png")
    return img_data


def ocr_from_image_bytes(image_bytes: bytes):
    # Convertir a imagen OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Ejecutar OCR
    result = ocr.ocr(img, cls=True)

    # Extraer líneas de texto en orden visual
    lines = []
    for line in result:
        for box, (text, prob) in line:
            clean = text.strip()
            if clean:
                lines.append(clean)

    full_text = "\n".join(lines)
    return full_text, lines


# ------------------------------
# EXTRACCIÓN DE CAMPOS CLAVE
# ------------------------------

def normalize_nit(raw):
    if not raw:
        return None
    # Extraer solo dígitos
    digits = re.sub(r'\D', '', raw)
    # Si tiene más de 9 dígitos, tomamos los primeros 9 (sin DV)
    if len(digits) >= 9:
        digits = digits[:9]
    return digits


def normalize_total(raw):
    if not raw:
        return None

    raw = raw.replace(".", "").replace(",", ".")
    try:
        return f"{float(raw):.2f}"
    except:
        return None


def extract_fields(full_text):
    # ---------------- NIT -----------------
    nit_match = re.search(
        r'(?:NIT|HIT|NIF)[\s:.-]*([\d\.\- ]+)',
        full_text, re.IGNORECASE
    )
    nit = normalize_nit(nit_match.group(1)) if nit_match else None

    # ---------------- FACTURA / NUMERO  -----------------
    num_match = re.search(
        r'(FACTURA(?: ELECTR[oÓ]NICA)?(?: DE VENTA)?|No\.?|N°|#)\s*[:\-]?\s*([A-Za-z0-9\-\./]+)',
        full_text, re.IGNORECASE
    )
    numero_factura = num_match.group(2) if num_match else None

    # ---------------- FECHA -----------------
    fecha_match = re.search(
        r'(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})',
        full_text
    )
    fecha = dateparser.parse(fecha_match.group(1)).strftime("%Y-%m-%d") if fecha_match else None

    # ---------------- TOTAL (con prioridad correcta) -----------------
    # 1. Buscar TOTAL A PAGAR o TOTAL NETO (más confiables)
    total_match = re.search(
        r'(TOTAL\s*(A\s*PAGAR|NETO|VENTA|:)?)[^\d]*([\d\.,]+)',
        full_text, re.IGNORECASE
    )

    if total_match:
        total = normalize_total(total_match.group(3))
    else:
        # Si no encontramos total claro, buscar SUBTOTAL
        subtotal_match = re.search(r'SUBTOTAL[^\d]*([\d\.,]+)', full_text, re.IGNORECASE)
        total = normalize_total(subtotal_match.group(1)) if subtotal_match else None

    return {
        "nit_proveedor": nit,
        "numero_factura": numero_factura,
        "fecha": fecha,
        "total": total
    }



# ------------------------------
# PROCESAMIENTO COMPLETO
# ------------------------------

def procesar_documento(file_bytes, filename):
    # Detectar si es PDF
    if file_bytes[:4] == b'%PDF':
        file_bytes = pdf_to_image_bytes(file_bytes)

    full_text, lines = ocr_from_image_bytes(file_bytes)

    campos = extract_fields(full_text)

    return {
        "filename": filename,
        **campos,
        "full_text": full_text,
        "lines": lines
    }
