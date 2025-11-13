"""
Tokenizer helper utilities for text chunking.
"""

import re
import logging
from typing import Generator, Optional, Any

logger = logging.getLogger(__name__)


class TokenizerHelper:
    """Helper class for token-based text chunking."""
    
    @staticmethod
    def count_tokens(text: str, tokenizer: Optional[Any] = None) -> int:
        """
        Count tokens in a text segment.
        
        Args:
            text: Text to count tokens for
            tokenizer: Optional tokenizer object with encode method
            
        Returns:
            Number of tokens
        """
        if tokenizer:
            try:
                return len(tokenizer.encode(text, add_special_tokens=False))
            except Exception as e:
                logger.warning(f"Token counting failed with tokenizer: {e}, using fallback")
        
        # Fallback: character-based estimation (rough approximation: 1 token ≈ 4 characters)
        return int(len(text) * 0.25)
    
    @staticmethod
    def chunks(text: str, size: int = 512, tokenizer: Optional[Any] = None) -> Generator[str, None, None]:
        """
        Split text into chunks of specified token size.
        
        Args:
            text: Text content to chunk
            size: Maximum token size per chunk (default: 512)
            tokenizer: Optional tokenizer object for accurate token counting
            
        Yields:
            Text chunks that are within the token limit
        """
        if not text or not text.strip():
            return
        
        # Conservative chunk size (leave room for special tokens)
        chunk_size = size - 50  # Reserve 50 tokens for special tokens and safety margin
        
        def count_tokens(text_segment: str) -> int:
            """Count tokens in a text segment."""
            return TokenizerHelper.count_tokens(text_segment, tokenizer)
        
        def split_long_text(text: str, max_tokens: int) -> list:
            """Split text that exceeds token limit into smaller chunks."""
            if count_tokens(text) <= max_tokens:
                return [text]
            
            # Split by words and rebuild chunks
            words = text.split()
            chunks = []
            current_chunk = []
            
            for word in words:
                # Test if adding this word would exceed limit
                test_chunk = current_chunk + [word]
                test_text = ' '.join(test_chunk)
                test_tokens = count_tokens(test_text)
                
                if test_tokens > max_tokens and current_chunk:
                    # Save current chunk and start new one
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                else:
                    current_chunk.append(word)
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            return chunks
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_chunk_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = count_tokens(sentence)
            
            # If sentence itself exceeds limit, split it first
            if sentence_tokens > chunk_size:
                # Yield current chunk if it exists
                if current_chunk:
                    yield ' '.join(current_chunk)
                    current_chunk = []
                    current_chunk_tokens = 0
                
                # Split the long sentence and yield each part
                sentence_chunks = split_long_text(sentence, chunk_size)
                for chunk in sentence_chunks:
                    yield chunk
                continue
            
            # Check if adding this sentence would exceed limit
            if current_chunk_tokens + sentence_tokens > chunk_size and current_chunk:
                # Yield current chunk and start new one
                yield ' '.join(current_chunk)
                current_chunk = [sentence]
                current_chunk_tokens = sentence_tokens
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_chunk_tokens += sentence_tokens
        
        # Yield remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_tokens = count_tokens(chunk_text)
            
            # Validate chunk is within limit
            if chunk_tokens > size:
                # Split if still too large
                split_chunks = split_long_text(chunk_text, chunk_size)
                for chunk in split_chunks:
                    yield chunk
            else:
                yield chunk_text

