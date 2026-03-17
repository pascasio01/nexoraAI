import json
import os
import re
import sys
from typing import Any


def extraer_texto(path_imagen: str) -> str:
    import cv2
    import pytesseract

    imagen = cv2.imread(path_imagen)
    if imagen is None:
        raise ValueError(f"No se pudo leer la imagen: {path_imagen}")
    return pytesseract.image_to_string(imagen).strip()


def extraer_ips(texto: str) -> list[str]:
    patron_ip = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    candidatos = set(re.findall(patron_ip, texto))
    return sorted(ip for ip in candidatos if _es_ip_valida(ip))


def _es_ip_valida(ip: str) -> bool:
    partes = ip.split(".")
    return len(partes) == 4 and all(parte.isdigit() and 0 <= int(parte) <= 255 for parte in partes)


def consultar_shodan(ip: str, api_key: str) -> dict[str, Any]:
    import shodan

    cliente = shodan.Shodan(api_key)
    try:
        data = cliente.host(ip)
        return {
            "ip": ip,
            "organizacion": data.get("org"),
            "sistema_operativo": data.get("os"),
            "puertos": data.get("ports", []),
        }
    except shodan.APIError as exc:
        return {"ip": ip, "error": str(exc)}


def analizar_imagen(path_imagen: str, api_key: str | None = None) -> dict[str, Any]:
    if not os.path.exists(path_imagen):
        raise FileNotFoundError(f"No existe el archivo: {path_imagen}")

    texto = extraer_texto(path_imagen)
    ips = extraer_ips(texto)
    api_key = api_key or os.getenv("SHODAN_API_KEY", "")

    resultado: dict[str, Any] = {"imagen": path_imagen, "texto": texto, "ips": ips, "shodan": []}
    if not api_key:
        resultado["warning"] = "SHODAN_API_KEY no configurada"
        return resultado

    resultado["shodan"] = [consultar_shodan(ip, api_key) for ip in ips]
    return resultado


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python analizador.py <ruta_imagen>")
        return 1

    path_imagen = sys.argv[1]
    try:
        resultado = analizar_imagen(path_imagen)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Error en análisis OSINT de {path_imagen}: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
