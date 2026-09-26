import unittest
from unittest.mock import AsyncMock, patch
from agent_core.agent_engine import AgentEngine


class AgentReplyTests(unittest.IsolatedAsyncioTestCase):
    async def test_action_examples_in_code_do_not_execute(self):
        text = 'Example:\n```text\n[ACTION:play_music(query="example")]\n```'
        with patch('agent_core.agent_engine.execute_tool', new_callable=AsyncMock) as execute:
            reply, results = await AgentEngine.process_response(text, {})
        execute.assert_not_awaited()
        self.assertEqual(reply, text)
        self.assertEqual(results, [])

    async def test_regular_markdown_is_preserved(self):
        text = '- Step one\n- Step two\n\n**Explanation:**\n```python\nprint("ok")\n```'
        reply, results = await AgentEngine.process_response(text, {})
        self.assertEqual(reply, text)
