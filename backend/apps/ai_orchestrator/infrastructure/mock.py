from typing import Dict, Any, AsyncIterator
import asyncio
import random
from ..domain.ports import AIManager, Prompt, Completion

class MockProvider(AIManager):
    """
    Mock implementation for testing/development without GPU.
    Returns fast Persian responses for the medical chat.
    """
    
    # Persian mock responses for medical chat
    MOCK_RESPONSES = [
        "سلام! چه علائمی دارید؟ آیا تب، سرفه یا درد خاصی دارید؟",
        "برای کمک بهتر، لطفاً علائم خود را详细 توضیح دهید.",
        "این علائم ممکن است به دلایل مختلفی باشد. آیا سابقه بیماری خاصی دارید؟",
        "توصیه می‌کنم به پزشک عمومی مراجعه کنید تا معاینه شوید.",
        "آیا درد خاصی دارید؟ کجای بدن‌تان درد می‌کند؟",
        "آیا علائم دیگری مانند حالت تهوع، سرگیجه یا خستگی دارید؟",
        "بهتر است آزمایش خون انجام دهید تا وضعیت سلامتی‌تان مشخص شود.",
        "آیا در حال مصرف داروی خاصی هستید؟",
        "استراحت کافی داشته باشید و آب زیاد بنوشید.",
        "اگر علائم ادامه پیدا کرد، حتماً به پزشک مراجعه کنید."
    ]
    
    async def generate_response(self, prompt: Prompt) -> Completion:
        # Simulate slight delay
        await asyncio.sleep(0.01)
        response = random.choice(self.MOCK_RESPONSES)
        return Completion(
            content=response,
            model_used="mock-v1",
            raw_response={"status": "mocked"}
        )

    async def stream_response(self, prompt: Prompt) -> AsyncIterator[str]:
        # Select a random response and stream it word by word
        response = random.choice(self.MOCK_RESPONSES)
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Very fast streaming - 50ms per word

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "version": "1.0"
        }
