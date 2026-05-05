import unittest

from app.services.translation.clients import translator_factory as factory


class TranslatorFactoryTests(unittest.TestCase):
    def setUp(self):
        self._backend = factory.settings.TRANSLATOR_BACKEND
        self._openai_enabled = factory.settings.OPENAI_TRANSLATION_ENABLED
        self._deepl_enabled = factory.settings.DEEPL_TRANSLATION_ENABLED

    def tearDown(self):
        factory.settings.TRANSLATOR_BACKEND = self._backend
        factory.settings.OPENAI_TRANSLATION_ENABLED = self._openai_enabled
        factory.settings.DEEPL_TRANSLATION_ENABLED = self._deepl_enabled

    def test_defaults_to_openai(self):
        factory.settings.TRANSLATOR_BACKEND = "auto"
        factory.settings.OPENAI_TRANSLATION_ENABLED = True
        factory.settings.DEEPL_TRANSLATION_ENABLED = False

        translator = factory.get_translator_client()

        self.assertIsInstance(translator, factory.OpenAITranslator)

    def test_can_switch_to_deepl(self):
        factory.settings.TRANSLATOR_BACKEND = "auto"
        factory.settings.OPENAI_TRANSLATION_ENABLED = False
        factory.settings.DEEPL_TRANSLATION_ENABLED = True

        translator = factory.get_translator_client()

        self.assertIsInstance(translator, factory.DeepLClient)

    def test_forced_backend_string_still_works(self):
        factory.settings.TRANSLATOR_BACKEND = "deepl"
        factory.settings.OPENAI_TRANSLATION_ENABLED = True
        factory.settings.DEEPL_TRANSLATION_ENABLED = False

        translator = factory.get_translator_client()

        self.assertIsInstance(translator, factory.DeepLClient)


if __name__ == "__main__":
    unittest.main()
