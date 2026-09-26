import unittest
from chat_quality import clean_chat_reply, provider_messages, gemini_answer


class ChatQualityTests(unittest.TestCase):
    def test_preserves_code_bullets_and_paragraphs(self):
        text = '- First step\n- Second step\n\n```python\nif True:\n    print("hello")\n```'
        self.assertEqual(clean_chat_reply(text), text)

    def test_casual_chat_spacing_is_compact(self):
        sample = "Bas sab badhiya hai Bunny bhai! ❤️ Aapka intezaar hi kar rahi thi. 😊\n\nAur batao, aaj ka din kaisa raha aapka? Sab set hai na? ✨"
        expected = "Bas sab badhiya hai Bunny bhai! ❤️ Aapka intezaar hi kar rahi thi. 😊 Aur batao, aaj ka din kaisa raha aapka? Sab set hai na? ✨"
        self.assertEqual(clean_chat_reply(sample), expected)

    def test_hides_thoughts_without_losing_answer(self):
        self.assertEqual(clean_chat_reply('<think>private</think>\n**Answer:** 42'), '**Answer:** 42')

    def test_thought_only_response_is_empty(self):
        self.assertEqual(gemini_answer({'candidates': [{'content': {'parts': [
            {'text': 'private thoughts', 'thought': True}]}}]}), '')

    def test_code_example_tags_stay_literal(self):
        example = '```xml\n<think>example</think>\n```'
        self.assertEqual(clean_chat_reply(example), example)

    def test_gateway_preserves_followup_context(self):
        messages = provider_messages([
            {'role': 'user', 'parts': [{'text': 'My project is Python.'}]},
            {'role': 'model', 'parts': [{'text': 'Which version?'}]},
            {'role': 'user', 'parts': [{'text': '3.11'}]},
        ], 'Be helpful')
        self.assertEqual([m['role'] for m in messages], ['system', 'user', 'assistant', 'user'])
        self.assertEqual(messages[1]['content'], 'My project is Python.')

    def test_gateway_keeps_image_and_question(self):
        messages = provider_messages([{'role': 'user', 'parts': [
            {'inlineData': {'mimeType': 'image/png', 'data': 'abc'}},
            {'text': 'What is this?'}]}], 'system')
        self.assertEqual(messages[1]['content'][0]['image_url']['url'], 'data:image/png;base64,abc')
        self.assertEqual(messages[1]['content'][1]['text'], 'What is this?')
