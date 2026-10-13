import os
import json
import re
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


class LLMProvider(Enum):
    GROQ = "groq"
    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


@dataclass
class Document:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "web"


@dataclass
class ResearchState:
    question: str
    search_results: List[SearchResult] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    summaries: List[str] = field(default_factory=list)
    final_answer: str = ""
    sources: List[Dict[str, str]] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 3
    needs_more_search: bool = True
    error: Optional[str] = None


def extract_json_payload(text: str) -> Any:
    """Robustly extract and parse JSON from LLM text that may contain markdown or conversational formatting."""
    if not text:
        return None
    cleaned = text.strip()
    
    # 1. Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass
        
    # 2. Extract from markdown code fences ```json ... ``` or ``` ... ```
    fence_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    fence_matches = re.findall(fence_pattern, cleaned)
    for fm in fence_matches:
        try:
            return json.loads(fm.strip())
        except Exception:
            continue
            
    # 3. Find JSON array [ ... ]
    array_match = re.search(r'\[\s*(?:\{[\s\S]*\}|".*?"|[\d\w\.-]+)[\s\S]*?\]', cleaned)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except Exception:
            pass

    # 4. Find JSON object { ... }
    obj_match = re.search(r'\{[\s\S]*\}', cleaned)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except Exception:
            pass

    return None


class WebSearchTool:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()

    def search(self, query: str) -> List[SearchResult]:
        try:
            results = []
            for r in self.ddgs.text(query, max_results=self.max_results):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                    source="duckduckgo"
                ))
            return results
        except Exception as e:
            print(f"Search error for query '{query}': {e}")
            return []


class WebScraper:
    def __init__(self, timeout: int = 10, max_chars_per_doc: int = 2500):
        self.timeout = timeout
        self.max_chars_per_doc = max_chars_per_doc
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def scrape(self, url: str) -> Optional[Document]:
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form"]):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            clean_text = re.sub(r'\s+', ' ', text).strip()
            
            if len(clean_text) < 150:
                return None
                
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            
            # Bound content length to prevent TPM / context overflow on LLM API
            return Document(
                content=clean_text[:self.max_chars_per_doc],
                metadata={"url": url, "title": title},
                source="web"
            )
        except Exception as e:
            print(f"Scrape error for {url}: {e}")
            return None


def create_llm(provider: LLMProvider, model: str, api_key: str = "", temperature: float = 0.3, base_url: str = ""):
    """Create an LLM instance based on provider with sensible defaults and key fallbacks."""
    
    if provider == LLMProvider.GROQ:
        from langchain_groq import ChatGroq
        effective_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        # Fallback if old deprecated model requested
        if not model or "llama-3.1-70b-versatile" in model or "llama-3.1-8b-instant" in model:
            model = "openai/gpt-oss-20b"
        return ChatGroq(
            api_key=effective_key,
            model=model,
            temperature=temperature
        )
    
    elif provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI
        effective_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not model:
            model = "gpt-4o-mini"
        return ChatOpenAI(
            api_key=effective_key,
            model=model,
            temperature=temperature
        )
    
    elif provider == LLMProvider.OLLAMA:
        from langchain_ollama import ChatOllama
        if not model:
            model = "llama3.1"
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url or "http://localhost:11434"
        )
    
    elif provider == LLMProvider.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI
        effective_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        if not model:
            model = "gemini-1.5-flash"
        return ChatGoogleGenerativeAI(
            api_key=effective_key,
            model=model,
            temperature=temperature
        )
    
    raise ValueError(f"Unknown provider: {provider}")


def create_embeddings(provider: LLMProvider, api_key: str = ""):
    """Create embeddings instance lazily when required."""
    if provider in (LLMProvider.GROQ, LLMProvider.OLLAMA, LLMProvider.GEMINI):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            print(f"Could not initialize HuggingFace embeddings: {e}")
            return None
    else:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Could not initialize OpenAI embeddings: {e}")
            return None


class Summarizer:
    def __init__(self, llm):
        self.llm = llm

    def summarize(self, question: str, documents: List[Document]) -> str:
        if not documents:
            return "No documents to summarize."
        
        # Take the most recent documents and format excerpts cleanly
        doc_snippets = []
        for d in documents[-5:]:
            url = d.metadata.get('url', 'unknown')
            title = d.metadata.get('title', url)
            content_snippet = d.content[:1500]
            doc_snippets.append(f"Title: {title}\nURL: {url}\nExcerpt:\n{content_snippet}")
        
        combined = "\n\n---\n\n".join(doc_snippets)
        
        prompt = f"""You are an elite research analyst. Summarize key factual insights from the following web sources to address the research question.
Focus on verified facts, breakthroughs, data points, and answers.
Cite sources inline using [Source: Title/URL] format.

Research Question: {question}

Gathered Sources:
{combined}

Provide a concise, high-density analytical summary:"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content


class AnswerSynthesizer:
    def __init__(self, llm):
        self.llm = llm

    def synthesize(self, question: str, summaries: List[str], sources: List[Dict]) -> str:
        combined_summaries = "\n\n".join(summaries[-3:])
        sources_text = "\n".join([f"- {s.get('title', 'Source')}: {s.get('url', '')}" for s in sources[:10]])
        
        prompt = f"""You are a principal research scientist delivering an authoritative, comprehensive research briefing.

Research Question: {question}

Synthesized Evidence from Research Cycles:
{combined_summaries}

Verified Reference Sources:
{sources_text}

Produce a well-structured, professional research briefing in Markdown:
1. ### Executive Summary: Direct, punchy answer to the core question.
2. ### Key Findings & Mechanism: Technical details, recent data, and discoveries.
3. ### Industry Context & Future Outlook: Challenges, debates, and future milestones.
4. ### References & Citations: Format references inline using markdown links [Title](URL).

Research Briefing:"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content


class ResearchAgent:
    def __init__(
        self, 
        provider: LLMProvider = LLMProvider.GROQ,
        model: str = "openai/gpt-oss-20b",
        api_key: str = "",
        temperature: float = 0.3,
        ollama_base_url: str = ""
    ):
        self.provider = provider
        self.llm = create_llm(provider, model, api_key, temperature, ollama_base_url)
        self.search_tool = WebSearchTool(max_results=5)
        self.scraper = WebScraper(max_chars_per_doc=2500)
        self.summarizer = Summarizer(self.llm)
        self.synthesizer = AnswerSynthesizer(self.llm)
        self._embeddings = None
        self.vector_store = None
        
    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = create_embeddings(self.provider)
        return self._embeddings

    def plan_search(self, state: ResearchState, callback: Optional[Callable] = None) -> ResearchState:
        if state.iteration >= state.max_iterations:
            state.needs_more_search = False
            return state
            
        if callback:
            callback("plan_start", f"Cycle {state.iteration + 1}: Formulating strategic search queries...", {
                "iteration": state.iteration + 1,
                "max_iterations": state.max_iterations
            })
            
        prompt = f"""You are an autonomous research planner. Given the research topic and progress, generate 2 to 3 targeted web search queries to retrieve high-value information.

Research Question: {state.question}
Cycle: {state.iteration + 1}/{state.max_iterations}
Previous sources collected: {len(state.sources)}

Return ONLY a valid JSON array of query strings, e.g. ["query 1", "query 2"].
Queries:"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        parsed = extract_json_payload(response.content)
        
        if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed) and parsed:
            queries = parsed[:3]
        else:
            queries = [state.question]
        
        if callback:
            callback("queries_planned", f"Executing search queries: {', '.join(queries)}", {"queries": queries})
        
        all_results = []
        for query in queries:
            results = self.search_tool.search(query)
            all_results.extend(results)
            if callback:
                callback("search_query_done", f"Queried DuckDuckGo for: '{query}' ({len(results)} matches)", {
                    "query": query,
                    "matches": len(results)
                })
        
        seen_urls = {r.url for r in state.search_results}
        unique_results = []
        for r in all_results:
            if r.url and r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)
        
        state.search_results.extend(unique_results[:8])
        return state

    def scrape_sources(self, state: ResearchState, callback: Optional[Callable] = None) -> ResearchState:
        new_docs = []
        # Target recent candidates
        candidates = state.search_results[-(4 + state.iteration * 2):]
        
        if callback:
            callback("scrape_start", f"Scraping {len(candidates)} candidate web sources...", {"candidates": len(candidates)})
            
        for result in candidates:
            doc = self.scraper.scrape(result.url)
            if doc:
                new_docs.append(doc)
                state.sources.append({
                    "title": result.title or doc.metadata.get("title", "Web Source"),
                    "url": result.url,
                    "snippet": result.snippet[:250] if result.snippet else doc.content[:200]
                })
                if callback:
                    callback("source_scraped", f"Extracted content from: {result.title[:45]}...", {"url": result.url})
        
        state.documents.extend(new_docs)
        return state

    def summarize_documents(self, state: ResearchState, callback: Optional[Callable] = None) -> ResearchState:
        if not state.documents:
            state.summaries.append("No documents retrieved.")
            return state
        
        if callback:
            callback("summarize_start", "Extracting key findings and evidence from sources...", {})
            
        summary = self.summarizer.summarize(state.question, state.documents)
        state.summaries.append(summary)
        
        if callback:
            callback("summarize_done", "Synthesized research findings for current cycle.", {})
            
        return state

    def evaluate_completeness(self, state: ResearchState, callback: Optional[Callable] = None) -> ResearchState:
        if state.iteration >= state.max_iterations - 1:
            state.needs_more_search = False
            state.iteration += 1
            return state
            
        prompt = f"""Evaluate if current research answers the question with sufficient depth.

Research Question: {state.question}
Synthesized Findings:
{chr(10).join(state.summaries[-1:])}
Total Sources: {len(state.sources)}

Respond in valid JSON format:
{{"complete": true or false, "reason": "brief reason", "gaps": ["gap 1"]}}"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        parsed = extract_json_payload(response.content)
        
        if isinstance(parsed, dict) and "complete" in parsed:
            state.needs_more_search = not bool(parsed.get("complete", False))
            reason = parsed.get("reason", "Evaluation complete")
        else:
            state.needs_more_search = state.iteration < state.max_iterations - 1
            reason = f"Proceeding to cycle {state.iteration + 2}"
        
        state.iteration += 1
        if callback:
            callback("eval_done", f"Completeness check: {reason}", {"iteration": state.iteration, "needs_more": state.needs_more_search})
            
        return state

    def generate_final_answer(self, state: ResearchState, callback: Optional[Callable] = None) -> ResearchState:
        if callback:
            callback("synthesize_start", "Synthesizing authoritative final research briefing with citations...", {})
            
        state.final_answer = self.synthesizer.synthesize(
            state.question, state.summaries, state.sources
        )
        
        if callback:
            callback("synthesize_done", "Research briefing generated successfully!", {})
            
        return state

    def run(
        self, 
        question: str, 
        max_iterations: int = 3,
        callback: Optional[Callable[[str, str, Optional[Dict[str, Any]]], None]] = None
    ) -> ResearchState:
        initial_state = ResearchState(
            question=question,
            max_iterations=max_iterations
        )
        
        state = self.plan_search(initial_state, callback=callback)
        state = self.scrape_sources(state, callback=callback)
        state = self.summarize_documents(state, callback=callback)
        
        while state.needs_more_search and state.iteration < state.max_iterations:
            state = self.evaluate_completeness(state, callback=callback)
            if state.needs_more_search:
                state = self.plan_search(state, callback=callback)
                state = self.scrape_sources(state, callback=callback)
                state = self.summarize_documents(state, callback=callback)
        
        state = self.generate_final_answer(state, callback=callback)
        
        if callback:
            callback("complete", "All research phases finished.", {"total_sources": len(state.sources)})
            
        return state


def create_agent(
    provider: str = "groq",
    model: str = "",
    api_key: str = "",
    temperature: float = 0.3,
    ollama_base_url: str = ""
) -> ResearchAgent:
    """Factory function to create a ResearchAgent with specified provider."""
    
    if isinstance(provider, str):
        provider_enum = LLMProvider(provider.lower())
    else:
        provider_enum = provider
    
    default_models = {
        LLMProvider.GROQ: "openai/gpt-oss-20b",
        LLMProvider.OPENAI: "gpt-4o-mini",
        LLMProvider.OLLAMA: "llama3.1",
        LLMProvider.GEMINI: "gemini-1.5-flash"
    }
    
    if not model:
        model = default_models.get(provider_enum, "openai/gpt-oss-20b")
    
    return ResearchAgent(
        provider=provider_enum,
        model=model,
        api_key=api_key,
        temperature=temperature,
        ollama_base_url=ollama_base_url
    )


# Backward compatibility
def create_agent_legacy(api_key: str, model: str = "openai/gpt-oss-20b") -> ResearchAgent:
    return create_agent(provider="groq", model=model, api_key=api_key)