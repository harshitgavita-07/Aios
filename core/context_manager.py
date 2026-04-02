"""
Context Manager — Intelligent context window management
Balances memory, RAG, and current conversation context.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

log = logging.getLogger("aios.context")


@dataclass
class ContextFragment:
    """A piece of context with metadata."""
    content: str
    source: str  # "memory", "rag", "web", "system"
    relevance_score: float
    timestamp: str
    token_estimate: int


class ContextManager:
    """
    Manages the context window for LLM prompts.
    
    Change: Intelligent context prioritization
    Why:
    - Previous system used simple last-N messages
    - Context window is limited and valuable
    - Need to prioritize most relevant information
    Impact:
    - Better token utilization
    - More relevant context in prompts
    """

    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens
        self.tokens_per_message = 4  # rough estimate overhead
        self.tokens_per_char = 0.25  # rough estimate
        
        # Priority weights
        self.source_weights = {
            "system": 1.0,
            "user_current": 0.95,
            "tool_result": 0.9,
            "memory_recent": 0.8,
            "rag_high": 0.75,
            "web_fresh": 0.7,
            "memory_older": 0.5,
            "rag_low": 0.3,
        }
        
        log.info(f"ContextManager initialized (max_tokens={max_tokens})")

    def build_context(self,
                     user_query: str,
                     memory_messages: List[Dict],
                     rag_results: Optional[List[Dict]] = None,
                     web_results: Optional[List[Dict]] = None,
                     tool_results: Optional[List[Dict]] = None,
                     system_prompt: str = "") -> List[Dict[str, str]]:
        """
        Build optimized context for LLM.
        
        Change: Multi-source context prioritization
        Why:
        - Different sources have different value
        - Recent web data > old memory for some queries
        - System prompt is critical
        Impact:
        - Smarter context window usage
        - Better response quality
        """
        fragments: List[ContextFragment] = []
        
        # Add system prompt (highest priority)
        if system_prompt:
            fragments.append(ContextFragment(
                content=system_prompt,
                source="system",
                relevance_score=1.0,
                timestamp="",
                token_estimate=self._estimate_tokens(system_prompt)
            ))
        
        # Add current user query
        fragments.append(ContextFragment(
            content=user_query,
            source="user_current",
            relevance_score=0.95,
            timestamp="",
            token_estimate=self._estimate_tokens(user_query)
        ))
        
        # Add memory messages (scored by recency)
        for i, msg in enumerate(reversed(memory_messages[-10:])):
            recency_decay = 0.9 ** i
            fragments.append(ContextFragment(
                content=f"{msg['role']}: {msg['content']}",
                source="memory_recent" if i < 3 else "memory_older",
                relevance_score=0.8 * recency_decay,
                timestamp=msg.get("timestamp", ""),
                token_estimate=self._estimate_tokens(msg["content"]) + self.tokens_per_message
            ))
        
        # Add RAG results
        if rag_results:
            for result in rag_results:
                score = result.get("score", 0.5)
                source_type = "rag_high" if score > 0.7 else "rag_low"
                fragments.append(ContextFragment(
                    content=result.get("content", ""),
                    source=source_type,
                    relevance_score=score,
                    timestamp=result.get("timestamp", ""),
                    token_estimate=self._estimate_tokens(result.get("content", ""))
                ))
        
        # Add web results
        if web_results:
            for result in web_results[:3]:  # Top 3 web results
                fragments.append(ContextFragment(
                    content=result.get("content", ""),
                    source="web_fresh",
                    relevance_score=0.7,
                    timestamp=result.get("timestamp", ""),
                    token_estimate=self._estimate_tokens(result.get("content", ""))
                ))
        
        # Add tool execution results
        if tool_results:
            for result in tool_results:
                tool_name = result.get("tool", "unknown")
                tool_output = result.get("result", {})
                if isinstance(tool_output, dict) and tool_output.get("success"):
                    content = f"Tool '{tool_name}' executed successfully: {tool_output.get('output', '')}"
                else:
                    content = f"Tool '{tool_name}' execution result: {str(tool_output)}"
                
                fragments.append(ContextFragment(
                    content=content,
                    source="tool_result",
                    relevance_score=0.9,  # High priority for tool results
                    timestamp="",
                    token_estimate=self._estimate_tokens(content)
                ))
        
        # Sort by weighted relevance
        fragments.sort(key=lambda f: f.relevance_score * self.source_weights.get(f.source, 0.5), reverse=True)
        
        # Build final context within token limit
        selected = []
        total_tokens = 0
        
        # Always include system and user
        system_frag = next((f for f in fragments if f.source == "system"), None)
        user_frag = next((f for f in fragments if f.source == "user_current"), None)
        
        if system_frag:
            selected.append(system_frag)
            total_tokens += system_frag.token_estimate
        
        if user_frag:
            selected.append(user_frag)
            total_tokens += user_frag.token_estimate
        
        # Add remaining fragments by priority
        for frag in fragments:
            if frag in selected:
                continue
            
            if total_tokens + frag.token_estimate < self.max_tokens * 0.9:  # Leave 10% buffer
                selected.append(frag)
                total_tokens += frag.token_estimate
            else:
                break
        
        # Convert to LLM message format
        messages = []
        system_content = "\n\n".join([f.content for f in selected if f.source == "system"])
        if system_content:
            messages.append({"role": "system", "content": system_content})
        
        # Combine context fragments into a single context message
        context_parts = []
        for frag in selected:
            if frag.source in ["rag_high", "rag_low", "web_fresh"]:
                prefix = "[Web]" if frag.source == "web_fresh" else "[Knowledge]"
                context_parts.append(f"{prefix} {frag.content}")
        
        if context_parts:
            context_msg = "Relevant information:\n" + "\n---\n".join(context_parts)
            messages.append({"role": "system", "content": context_msg})
        
        # Add memory as history
        memory_frags = [f for f in selected if f.source.startswith("memory")]
        for frag in memory_frags:
            if ": " in frag.content:
                role, content = frag.content.split(": ", 1)
                if role in ["user", "assistant"]:
                    messages.append({"role": role, "content": content})
        
        # Add current user query
        messages.append({"role": "user", "content": user_query})
        
        log.debug(f"Built context: {len(messages)} messages, ~{total_tokens} tokens")
        return messages

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation."""
        return int(len(text) * self.tokens_per_char) + self.tokens_per_message

    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        return {
            "max_tokens": self.max_tokens,
            "source_weights": self.source_weights,
        }
