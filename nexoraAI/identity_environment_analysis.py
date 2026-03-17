import json
from pathlib import Path
from typing import Any, Dict, List


def _safe_ocr_read(image_path: str) -> List[str]:
    """
    Extrae texto visible de una imagen solo si las dependencias OCR están disponibles.
    Si no puede procesar la imagen, devuelve una lista vacía.
    """
    image_file = Path(image_path)
    if not image_file.exists() or not image_file.is_file():
        return []

    try:
        import cv2  # type: ignore
        import pytesseract  # type: ignore
    except Exception:
        return []

    img = cv2.imread(str(image_file))
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return [line.strip() for line in text.splitlines() if line.strip()]


def analizar_identidad_y_entorno(ruta_imagen: str, ciudad: str = "New York") -> str:
    """
    Genera un reporte seguro a partir de una imagen.

    Nota de seguridad: esta función no realiza búsquedas de infraestructura sensible
    (por ejemplo, cámaras o dispositivos expuestos) para evitar usos invasivos.
    """
    datos_ocr = _safe_ocr_read(ruta_imagen)

    reporte: Dict[str, Any] = {
        "sujeto": {
            "datos_ocr": datos_ocr,
            "status": "Analizado" if datos_ocr else "Sin datos OCR",
        },
        "entorno_vigilancia": {
            "localizacion": ciudad,
            "camaras_disponibles": [],
            "status": "Bloqueado por seguridad",
            "mensaje": (
                "La búsqueda automatizada de cámaras/dispositivos en internet "
                "está deshabilitada por seguridad."
            ),
        },
    }

    return json.dumps(reporte, indent=4, ensure_ascii=False)
