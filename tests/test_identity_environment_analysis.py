import json
from pathlib import Path
import tempfile
import unittest

from nexoraAI.identity_environment_analysis import analizar_identidad_y_entorno


class TestIdentityEnvironmentAnalysis(unittest.TestCase):
    def test_returns_secure_report_structure(self):
        missing_file = Path(tempfile.gettempdir()) / "archivo_que_no_existe.png"
        raw = analizar_identidad_y_entorno(str(missing_file), "Santo Domingo")
        data = json.loads(raw)

        self.assertIn("sujeto", data)
        self.assertIn("entorno_vigilancia", data)
        self.assertEqual(data["entorno_vigilancia"]["localizacion"], "Santo Domingo")
        self.assertEqual(data["entorno_vigilancia"]["camaras_disponibles"], [])
        self.assertEqual(data["entorno_vigilancia"]["status"], "Bloqueado por seguridad")

    def test_handles_missing_image_without_crashing(self):
        missing_file = Path(tempfile.gettempdir()) / "imagen_inexistente.jpg"
        raw = analizar_identidad_y_entorno(str(missing_file))
        data = json.loads(raw)

        self.assertEqual(data["sujeto"]["datos_ocr"], [])
        self.assertEqual(data["sujeto"]["status"], "Sin datos OCR")


if __name__ == "__main__":
    unittest.main()
