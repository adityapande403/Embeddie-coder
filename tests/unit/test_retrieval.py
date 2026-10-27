"""
Unit tests for local technical documentation indexing and retrieval (RAG).
"""

import tempfile
from pathlib import Path
from embeddedcoder.retrieval.rag import LocalDocIndexer


def test_doc_indexer_chunking_and_retrieval():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "stm32_usart.txt"
        doc_path.write_text("""
## Section: USART Interrupt Configuration
The USART interrupt is triggered when the TXE (Transmit Data Register Empty) or RXNE (Read Data Register Not Empty) flags are set.
To enable RXNE interrupts, set the RXNEIE bit in the USART_CR1 control register.

## Section: Baud Rate Calculation
The baud rate register USART_BRR is computed as:
BRR = f_CK / (16 * BaudRate)
For a 16 MHz clock and 115200 baud, USART_BRR = 0x008B (8.6875).
""", encoding="utf-8")

        indexer = LocalDocIndexer()
        chunks = indexer.add_document(doc_path, doc_id="STM32F4-RM0090", chunk_lines=10)
        assert chunks > 0

        # Query for baud rate calculation
        results = indexer.retrieve("how to calculate USART_BRR baud rate")
        assert len(results) > 0
        best_passage, score = results[0]
        assert "USART_BRR" in best_passage.content
        assert "STM32F4-RM0090" in best_passage.citation()


def test_grounded_prompt_formatting():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "i2c_spec.txt"
        doc_path.write_text("In Standard Mode, I2C clock frequency is up to 100 kHz. In Fast Mode, clock is 400 kHz.", encoding="utf-8")

        indexer = LocalDocIndexer()
        indexer.add_document(doc_path, doc_id="I2C-SPEC")
        prompt, citations = indexer.format_grounded_prompt("What is I2C Fast Mode speed?", top_k=1)
        assert len(citations) == 1
        assert "400 kHz" in prompt
        assert "TECHNICAL DOCUMENTATION PASSAGE" in prompt
