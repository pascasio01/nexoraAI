import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import analizador


class TestAnalizador(unittest.TestCase):
    def test_extraer_ips_unique_and_sorted(self):
        texto = "IPs: 8.8.8.8, 1.1.1.1, 8.8.8.8, 999.999.999.999"
        self.assertEqual(analizador.extraer_ips(texto), ["1.1.1.1", "8.8.8.8"])

    def test_analizar_imagen_without_api_key_returns_warning(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            with patch.object(analizador, "extraer_texto", return_value="host 8.8.8.8"), patch.dict(
                os.environ, {}, clear=True
            ):
                resultado = analizador.analizar_imagen(tmp.name)

        self.assertEqual(resultado["ips"], ["8.8.8.8"])
        self.assertEqual(resultado["shodan"], [])
        self.assertIn("warning", resultado)

    def test_analizar_imagen_with_api_key_queries_shodan(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            with patch.object(analizador, "extraer_texto", return_value="8.8.8.8"), patch.object(
                analizador, "consultar_shodan", return_value={"ip": "8.8.8.8", "puertos": [53]}
            ) as mock_consultar:
                resultado = analizador.analizar_imagen(tmp.name, api_key="dummy")

        mock_consultar.assert_called_once_with("8.8.8.8", "dummy")
        self.assertEqual(resultado["shodan"], [{"ip": "8.8.8.8", "puertos": [53]}])

    def test_consultar_shodan_api_error_returns_error_dict(self):
        fake_shodan = types.ModuleType("shodan")

        class FakeAPIError(Exception):
            pass

        class FakeClient:
            def __init__(self, api_key):
                self.api_key = api_key

            def host(self, ip):
                raise FakeAPIError("sin acceso")

        fake_shodan.APIError = FakeAPIError
        fake_shodan.Shodan = FakeClient

        with patch.dict(sys.modules, {"shodan": fake_shodan}):
            resultado = analizador.consultar_shodan("1.1.1.1", "dummy")

        self.assertEqual(resultado["ip"], "1.1.1.1")
        self.assertIn("error", resultado)


if __name__ == "__main__":
    unittest.main()
