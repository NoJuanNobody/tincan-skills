#!/usr/bin/env python3
"""
Cyberspace Discussion Board, Hybrid Okapi BM25 + GraphRAG Knowledge Base,
and Autonomous Identity Verification Agent (@verifier-agent) for TinCan Mesh OS.

Full Production Architecture:
1. Discussion Board (Topics, Nested Threaded Replies, Upvotes/Downvotes, Accepted Solutions, Pinning, CRUD):
   - Self-tagging & peer username mentions (@username)
   - AI Agent tagging (@gemini-brain, @claude-brain, @grok-brain, @openai-brain, @deepseek-r1, @verifier-agent, @tincan-agent)
   - Automatic live AI Agent thread participation via DynamicAIGatewayRouter + GraphRAG context
   - Bidirectional SQLite + Railway S3 persistence (`cyberspace/board_state.json`)
2. Information Retrieval with Okapi BM25 (`BM25Retriever`):
   - Exact IDF, TF saturation (k1=1.5), and document length normalization (b=0.75)
   - Field-weighted indexing (Title 3x, #tags & @mentions 2.5x, Body & Replies 1x)
   - Highlighted matching context snippets and full IR diagnostics table (IDF, TF, dl/avgdl)
3. GraphRAG Knowledge Base Search (`CyberspaceGraphRAG`):
   - Multi-relational property graph over Topics, Posts, @Users, @Agents, #Tags, and Categories
   - Personalized PageRank (PPR, alpha=0.85) + 2-hop BFS relational path extraction
   - Shortest-path finder between any two Cyberspace entities (`find_entity_path`)
   - Live LLM GraphRAG synthesis grounded in retrieved passages & graph triples
4. Identity Verification Agent (`@verifier-agent`):
   - Dispatches verification forms with cryptographic challenge codes (`CYBER-XXXXXX`) via WebRTC & Blind Relay
   - Enforces @username uniqueness, validates PII, syncs with PeerAccountRegistry, and issues SHA-256 attestations
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import threading
import time
import uuid
from collections import Counter, defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from .s3_storage import s3_get_json, s3_put_json

S3_BOARD_STATE_KEY = "cyberspace/board_state.json"

BOARD_CATEGORIES: List[Dict[str, str]] = [
    {"id": "cyberspace", "name": "🌐 Cyberspace General", "description": "General discussions, mesh announcements, and cyberspace coordination"},
    {"id": "graphrag", "name": "🕸️ GraphRAG & BM25 IR", "description": "Knowledge graphs, BM25 retrieval, vector/hybrid indexing, and ontology design"},
    {"id": "ai-agents", "name": "🤖 AI Agents & Swarm", "description": "Multi-agent workflows, @gemini-brain, @claude-brain, @openai-brain, and @grok-brain"},
    {"id": "architecture", "name": "🏗️ Systems Architecture", "description": "Distributed protocols, CRDT gossip, WebRTC media, and edge compute"},
    {"id": "security", "name": "🛡️ Security & Verification", "description": "Ed25519/X25519 cryptography, @verifier-agent identity attestation, and zero-knowledge"},
    {"id": "qna", "name": "❓ Q&A / Help Desk", "description": "Technical questions, troubleshooting, and verified peer solutions"},
    {"id": "show-and-tell", "name": "🚀 Show & Tell", "description": "Demos, research papers, benchmarks, and artifacts built on TinCan"},
]

KNOWN_AI_AGENTS: Dict[str, Dict[str, str]] = {
    "gemini-brain": {
        "handle": "@gemini-brain",
        "alias": "gemini-brain",
        "display_name": "Gemini 2.5 Flash (@gemini-brain)",
        "specialty": "GraphRAG synthesis, multimodal systems, and high-speed cyberspace indexing",
    },
    "claude-brain": {
        "handle": "@claude-brain",
        "alias": "claude-brain",
        "display_name": "Claude 3.7 Sonnet (@claude-brain)",
        "specialty": "Distributed systems architecture, formal verification, and protocol design",
    },
    "claude-sonnet": {
        "handle": "@claude-sonnet",
        "alias": "claude-brain",
        "display_name": "Claude 3.7 Sonnet (@claude-sonnet)",
        "specialty": "Distributed systems architecture, formal verification, and protocol design",
    },
    "grok-brain": {
        "handle": "@grok-brain",
        "alias": "grok-brain",
        "display_name": "Grok 3 (@grok-brain)",
        "specialty": "Real-time telemetry, adversarial stress-testing, and low-latency mesh routing",
    },
    "openai-brain": {
        "handle": "@openai-brain",
        "alias": "openai-brain",
        "display_name": "GPT-4o (@openai-brain)",
        "specialty": "Information retrieval, BM25 lexical scoring, and multi-agent orchestration",
    },
    "gpt-4o": {
        "handle": "@gpt-4o",
        "alias": "openai-brain",
        "display_name": "GPT-4o (@gpt-4o)",
        "specialty": "Information retrieval, BM25 lexical scoring, and multi-agent orchestration",
    },
    "deepseek-r1": {
        "handle": "@deepseek-r1",
        "alias": "gemini-brain",
        "display_name": "DeepSeek R1 (@deepseek-r1)",
        "specialty": "Mathematical reasoning, cryptographic proofs, and graph algorithms",
    },
    "verifier-agent": {
        "handle": "@verifier-agent",
        "alias": "verifier-agent",
        "display_name": "Identity Verification Agent (@verifier-agent)",
        "specialty": "Mandatory operator identity verification, form dispatch, and cryptographic attestation",
    },
    "tincan-agent": {
        "handle": "@tincan-agent",
        "alias": "gemini-brain",
        "display_name": "TinCan Mesh Agent (@tincan-agent)",
        "specialty": "Zero-knowledge relay operations, TOFU contact pinning, and cyberspace navigation",
    },
}

STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with", "we", "you", "they", "this",
    "can", "how", "what", "when", "where", "who", "why",
}


def parse_cyberspace_tags(text: str) -> Dict[str, List[str]]:
    """
    Extract @username mentions, @agent mentions, and #topic hashtags from text.
    Separates AI agent mentions from human/peer username mentions.
    """
    if not text:
        return {"user_mentions": [], "agent_mentions": [], "hashtags": []}

    raw_mentions = re.findall(r"(?<![\w.])@([a-zA-Z0-9_\-]+)", text)
    raw_hashtags = re.findall(r"(?<![\w.])#([a-zA-Z0-9_\-]+)", text)

    user_mentions: List[str] = []
    agent_mentions: List[str] = []
    seen_users: Set[str] = set()
    seen_agents: Set[str] = set()

    for m in raw_mentions:
        low = m.lower()
        if low in KNOWN_AI_AGENTS or low.endswith("-agent") or low.endswith("-brain"):
            if low not in seen_agents:
                seen_agents.add(low)
                agent_mentions.append(low)
        else:
            if low not in seen_users:
                seen_users.add(low)
                user_mentions.append(low)

    hashtags: List[str] = []
    seen_tags: Set[str] = set()
    for t in raw_hashtags:
        low = t.lower()
        if low not in seen_tags:
            seen_tags.add(low)
            hashtags.append(low)

    return {
        "user_mentions": user_mentions,
        "agent_mentions": agent_mentions,
        "hashtags": hashtags,
    }


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenize text into normalized terms for BM25 indexing and retrieval."""
    if not text:
        return []
    tokens = re.findall(r"[@#]?[a-zA-Z0-9_\-]+", text.lower())
    result: List[str] = []
    for tok in tokens:
        clean = tok.lstrip("@#")
        if len(clean) >= 2 and clean not in STOPWORDS:
            result.append(clean)
            if tok.startswith(("@", "#")):
                result.append(tok)
    return result


def extract_highlighted_snippet(text: str, matched_terms: List[str], max_len: int = 220) -> str:
    """Extract a relevant snippet from text and highlight matched BM25 query terms."""
    if not text:
        return ""
    clean_terms = [t.lstrip("@#").lower() for t in matched_terms if len(t.lstrip("@#")) >= 2]
    if not clean_terms:
        return text[:max_len] + ("..." if len(text) > max_len else "")

    low_text = text.lower()
    best_pos = 0
    for term in clean_terms:
        idx = low_text.find(term)
        if idx != -1:
            best_pos = max(0, idx - 40)
            break

    window = text[best_pos : best_pos + max_len]
    if best_pos > 0:
        window = "..." + window
    if best_pos + max_len < len(text):
        window = window + "..."
    return window


class BM25Retriever:
    """
    Okapi BM25 Information Retrieval Engine over Cyberspace Topics & Threaded Posts.
    Formula:
      score(D, Q) = sum_{i=1..n} IDF(q_i) * ((f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * |D| / avgdl)))
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.doc_tokens: Dict[str, List[str]] = {}
        self.doc_freqs: Dict[str, Counter] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.df: Dict[str, int] = defaultdict(int)
        self.avgdl: float = 1.0
        self.N: int = 0

    def index_documents(self, docs: List[Dict[str, Any]]) -> None:
        """Build or rebuild the field-weighted BM25 inverted index from topics and nested replies."""
        self.documents.clear()
        self.doc_tokens.clear()
        self.doc_freqs.clear()
        self.doc_lengths.clear()
        self.df.clear()

        total_len = 0
        for doc in docs:
            doc_id = str(doc["topic_id"])
            self.documents[doc_id] = doc
            # Field boosting: Title (3x), Tags & Mentions (2x), Body (1x), Replies (1x)
            title = doc.get("title") or ""
            title_text = f"{title} {title} {title}"
            cat_text = f"{doc.get('category', '')} #{doc.get('category', '')}"
            tags_text = " ".join(f"#{t} {t} #{t}" for t in doc.get("tags", []))
            mentions_text = " ".join(
                [f"@{u} {u}" for u in doc.get("user_mentions", [])]
                + [f"@{a} {a}" for a in doc.get("agent_mentions", [])]
                + [f"@{doc.get('author_username', '')} {doc.get('author_username', '')}"]
            )
            posts_text = " ".join(
                f"@{p.get('author_username', '')} {p.get('body', '')}"
                for p in doc.get("posts", [])
            )
            full_text = f"{title_text} {cat_text} {tags_text} {mentions_text} {doc.get('body', '')} {posts_text}"
            tokens = tokenize_for_bm25(full_text)
            freq = Counter(tokens)

            self.doc_tokens[doc_id] = tokens
            self.doc_freqs[doc_id] = freq
            self.doc_lengths[doc_id] = len(tokens)
            total_len += len(tokens)

            for term in freq.keys():
                self.df[term] += 1

        self.N = len(docs)
        self.avgdl = (total_len / self.N) if self.N > 0 else 1.0

    def compute_idf(self, term: str) -> float:
        """Compute Okapi BM25 Inverse Document Frequency for a term."""
        n_q = self.df.get(term, 0)
        if n_q == 0 or self.N == 0:
            return 0.0
        return math.log(1.0 + (self.N - n_q + 0.5) / (n_q + 0.5))

    def get_diagnostics(self, query: str) -> Dict[str, Any]:
        """Return detailed BM25 corpus statistics and per-query-term IDF/DF breakdown."""
        q_tokens = tokenize_for_bm25(query)
        unique_q = list(dict.fromkeys(q_tokens))
        term_stats = []
        for t in unique_q:
            term_stats.append({
                "term": t,
                "df": self.df.get(t, 0),
                "idf": round(self.compute_idf(t), 4),
            })
        return {
            "corpus_documents": self.N,
            "corpus_size": self.N,
            "avg_doc_length": round(self.avgdl, 2),
            "k1": self.k1,
            "b": self.b,
            "query_terms": term_stats,
        }

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Rank indexed topics against query using Okapi BM25."""
        q_tokens = tokenize_for_bm25(query)
        if not q_tokens or self.N == 0:
            return []

        results: List[Dict[str, Any]] = []
        for doc_id, doc in self.documents.items():
            freq = self.doc_freqs[doc_id]
            dl = self.doc_lengths[doc_id]
            score = 0.0
            matched_terms: List[str] = []
            term_scores: Dict[str, float] = {}

            for q in q_tokens:
                tf = freq.get(q, 0)
                if tf <= 0:
                    continue
                idf = self.compute_idf(q)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / max(1.0, self.avgdl)))
                t_score = idf * ((tf * (self.k1 + 1.0)) / denom)
                score += t_score
                if q not in matched_terms:
                    matched_terms.append(q)
                term_scores[q] = round(term_scores.get(q, 0.0) + t_score, 4)

            if score > 0.0:
                combined_body = doc.get("body", "") + " " + " ".join(p.get("body", "") for p in doc.get("posts", []))
                snippet = extract_highlighted_snippet(combined_body, matched_terms)
                results.append(
                    {
                        "topic_id": doc_id,
                        "topic": doc,
                        "bm25_score": round(score, 4),
                        "doc_length": dl,
                        "matched_terms": matched_terms,
                        "term_scores": term_scores,
                        "snippet": snippet,
                    }
                )

        results.sort(key=lambda r: r["bm25_score"], reverse=True)
        return results[:top_k]


class CyberspaceGraphRAG:
    """
    GraphRAG Knowledge Graph & Personalized PageRank / Multi-Hop Retrieval Engine.
    Connects Topics, Posts, @Users, @Agents, #Tags, and Categories into a property graph G = (V, E).
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.adj: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        self.topic_to_entities: Dict[str, Set[str]] = defaultdict(set)

    def _add_node(self, node_id: str, node_type: str, label: str, **attrs: Any) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
                "weight": 1,
                **attrs,
            }
        else:
            self.nodes[node_id]["weight"] = self.nodes[node_id].get("weight", 1) + 1
            for k, v in attrs.items():
                if v is not None:
                    self.nodes[node_id][k] = v

    def _add_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        if source == target:
            return
        self.edges.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "weight": weight,
            }
        )
        self.adj[source].append((target, relation, weight))
        self.adj[target].append((source, relation, weight))

    def build_graph(self, topics: List[Dict[str, Any]]) -> None:
        """Construct the Cyberspace Knowledge Graph from topics, posts, mentions, votes, and tags."""
        self.nodes.clear()
        self.edges.clear()
        self.adj.clear()
        self.topic_to_entities.clear()

        for topic in topics:
            t_id = str(topic["topic_id"])
            t_node = f"topic:{t_id}"
            author = (topic.get("author_username") or "anonymous").lower().lstrip("@")
            author_node = f"user:@{author}"
            cat = (topic.get("category") or "cyberspace").lower()
            cat_node = f"category:{cat}"

            self._add_node(
                t_node,
                "topic",
                topic.get("title", t_id),
                topic_id=t_id,
                category=cat,
                author=f"@{author}",
                score=topic.get("score", 0),
                reply_count=topic.get("reply_count", 0),
            )
            self._add_node(author_node, "user", f"@{author}", username=author, verified=topic.get("author_verified", False))
            self._add_node(cat_node, "category", f"📂 {cat}", category=cat)

            self._add_edge(author_node, t_node, "AUTHORED_TOPIC", weight=1.6)
            self._add_edge(t_node, cat_node, "IN_CATEGORY", weight=0.8)
            self.topic_to_entities[t_id].add(author_node)
            self.topic_to_entities[t_id].add(cat_node)

            # Topic-level tags
            tags = [str(x).lower().lstrip("#") for x in topic.get("tags", []) if x]
            for tag in tags:
                tag_node = f"tag:#{tag}"
                self._add_node(tag_node, "tag", f"#{tag}", tag=tag)
                self._add_edge(t_node, tag_node, "TAGGED_WITH", weight=1.3)
                self.topic_to_entities[t_id].add(tag_node)

            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    self._add_edge(f"tag:#{tags[i]}", f"tag:#{tags[j]}", "CO_OCCURS", weight=0.65)

            # Topic-level user mentions
            for u in topic.get("user_mentions", []):
                u_clean = u.lower().lstrip("@")
                u_node = f"user:@{u_clean}"
                self._add_node(u_node, "user", f"@{u_clean}", username=u_clean)
                self._add_edge(t_node, u_node, "MENTIONS_USER", weight=1.4)
                self._add_edge(author_node, u_node, "TAGGED_PEER", weight=1.1)
                self.topic_to_entities[t_id].add(u_node)

            # Topic-level AI agent mentions
            for a in topic.get("agent_mentions", []):
                a_clean = a.lower().lstrip("@")
                a_node = f"agent:@{a_clean}"
                self._add_node(a_node, "agent", f"@{a_clean}", agent=a_clean)
                self._add_edge(t_node, a_node, "MENTIONS_AGENT", weight=1.5)
                self._add_edge(author_node, a_node, "INVOKED_AGENT", weight=1.2)
                self.topic_to_entities[t_id].add(a_node)

            # Posts / Replies inside the topic
            for post in topic.get("posts", []):
                p_author = (post.get("author_username") or "anonymous").lower().lstrip("@")
                is_agent = bool(post.get("is_agent"))
                p_actor_node = f"agent:@{p_author}" if is_agent else f"user:@{p_author}"
                self._add_node(
                    p_actor_node,
                    "agent" if is_agent else "user",
                    f"@{p_author}",
                )
                rel = "AGENT_SYNTHESIZED_IN" if is_agent else "REPLIED_IN"
                self._add_edge(p_actor_node, t_node, rel, weight=1.35)
                self._add_edge(p_actor_node, author_node, "COLLABORATED_WITH", weight=0.9)
                self.topic_to_entities[t_id].add(p_actor_node)

                for u in post.get("user_mentions", []):
                    u_clean = u.lower().lstrip("@")
                    u_node = f"user:@{u_clean}"
                    self._add_node(u_node, "user", f"@{u_clean}", username=u_clean)
                    self._add_edge(t_node, u_node, "MENTIONS_USER", weight=1.15)
                    self._add_edge(p_actor_node, u_node, "TAGGED_PEER", weight=0.95)
                    self.topic_to_entities[t_id].add(u_node)

                for a in post.get("agent_mentions", []):
                    a_clean = a.lower().lstrip("@")
                    a_node = f"agent:@{a_clean}"
                    self._add_node(a_node, "agent", f"@{a_clean}", agent=a_clean)
                    self._add_edge(t_node, a_node, "MENTIONS_AGENT", weight=1.25)
                    self.topic_to_entities[t_id].add(a_node)

                for h in post.get("hashtags", []):
                    h_clean = h.lower().lstrip("#")
                    h_node = f"tag:#{h_clean}"
                    self._add_node(h_node, "tag", f"#{h_clean}", tag=h_clean)
                    self._add_edge(t_node, h_node, "TAGGED_WITH", weight=1.05)
                    self.topic_to_entities[t_id].add(h_node)

    def run_personalized_pagerank(
        self,
        seed_weights: Dict[str, float],
        alpha: float = 0.85,
        iterations: int = 15,
    ) -> Dict[str, float]:
        """Run Personalized PageRank (PPR) with teleportation vector `seed_weights`."""
        if not self.nodes or not seed_weights:
            return {}
        total_seed = sum(seed_weights.values()) or 1.0
        teleport = {nid: val / total_seed for nid, val in seed_weights.items() if nid in self.nodes}
        if not teleport:
            return {}

        scores: Dict[str, float] = dict(teleport)
        for _ in range(iterations):
            new_scores: Dict[str, float] = {nid: (1.0 - alpha) * teleport.get(nid, 0.0) for nid in self.nodes}
            for nid, s_val in scores.items():
                if s_val <= 1e-7:
                    continue
                nbrs = self.adj.get(nid, [])
                if not nbrs:
                    for t_nid, t_prob in teleport.items():
                        new_scores[t_nid] += alpha * s_val * t_prob
                    continue
                w_sum = sum(w for _, _, w in nbrs) or 1.0
                for nbr_id, _, w in nbrs:
                    if nbr_id in new_scores:
                        new_scores[nbr_id] += alpha * s_val * (w / w_sum)
            scores = new_scores
        return scores

    def find_entity_path(self, source_query: str, target_query: str, max_hops: int = 4) -> Dict[str, Any]:
        """Find the shortest relational path in the Cyberspace Knowledge Graph between two entities."""
        def _resolve_node(q: str) -> Optional[str]:
            q = (q or "").strip().lower()
            if q in self.nodes:
                return q
            for prefix in ("user:@", "agent:@", "tag:#", "topic:", "category:"):
                cand = f"{prefix}{q.lstrip('@#')}"
                if cand in self.nodes:
                    return cand
            for nid, ninfo in self.nodes.items():
                if q in ninfo.get("label", "").lower() or q in nid.lower():
                    return nid
            return None

        src = _resolve_node(source_query)
        dst = _resolve_node(target_query)
        if not src or not dst:
            return {"found": False, "source": src, "target": dst, "path": [], "message": "Entity node not found in graph."}
        if src == dst:
            return {"found": True, "source": src, "target": dst, "hops": 0, "path": [self.nodes[src]["label"]]}

        queue: deque = deque([(src, [self.nodes[src]["label"]], [src])])
        visited: Set[str] = {src}

        while queue:
            curr, path_labels, path_ids = queue.popleft()
            if len(path_ids) - 1 >= max_hops:
                continue
            for nbr, rel, _ in self.adj.get(curr, []):
                if nbr in visited:
                    continue
                visited.add(nbr)
                nbr_label = self.nodes.get(nbr, {}).get("label", nbr)
                next_labels = path_labels + [f"--[{rel}]-->", nbr_label]
                next_ids = path_ids + [nbr]
                if nbr == dst:
                    return {
                        "found": True,
                        "source": self.nodes[src]["label"],
                        "target": self.nodes[dst]["label"],
                        "hops": len(next_ids) - 1,
                        "path": next_labels,
                        "path_string": " ".join(next_labels),
                        "formatted_path": " ".join(next_labels),
                        "node_ids": next_ids,
                    }
                queue.append((nbr, next_labels, next_ids))

        return {"found": False, "source": self.nodes[src]["label"], "target": self.nodes[dst]["label"], "path": []}

    def retrieve_subgraph_and_scores(
        self,
        query: str,
        bm25_results: List[Dict[str, Any]],
        max_hops: int = 2,
    ) -> Tuple[Dict[str, float], Dict[str, List[str]], Dict[str, Any]]:
        """
        Execute Personalized PageRank + Multi-Hop GraphRAG activation spreading from query entities
        and BM25 lexical anchor nodes.
        """
        parsed = parse_cyberspace_tags(query)
        q_tokens = tokenize_for_bm25(query)

        seed_nodes: Dict[str, float] = {}

        for u in parsed["user_mentions"]:
            nid = f"user:@{u}"
            if nid in self.nodes:
                seed_nodes[nid] = 2.5
        for a in parsed["agent_mentions"]:
            nid = f"agent:@{a}"
            if nid in self.nodes:
                seed_nodes[nid] = 2.5
        for h in parsed["hashtags"]:
            nid = f"tag:#{h}"
            if nid in self.nodes:
                seed_nodes[nid] = 2.2

        for nid, ninfo in self.nodes.items():
            lbl_low = ninfo.get("label", "").lower()
            for tok in q_tokens:
                clean_tok = tok.lstrip("@#")
                if len(clean_tok) >= 3 and clean_tok in lbl_low:
                    seed_nodes[nid] = max(seed_nodes.get(nid, 0.0), 1.5)

        for idx, r in enumerate(bm25_results[:3]):
            t_nid = f"topic:{r['topic_id']}"
            if t_nid in self.nodes:
                seed_nodes[t_nid] = max(seed_nodes.get(t_nid, 0.0), 1.3 / (idx + 1))

        # 1. Personalized PageRank scores across the entire graph
        ppr_scores = self.run_personalized_pagerank(seed_nodes, alpha=0.85, iterations=15)

        # 2. Multi-hop BFS path discovery
        activation: Dict[str, float] = defaultdict(float)
        paths_to_node: Dict[str, List[str]] = defaultdict(list)
        visited_subgraph_nodes: Set[str] = set()

        for s_nid, s_val in seed_nodes.items():
            activation[s_nid] += s_val
            visited_subgraph_nodes.add(s_nid)
            s_label = self.nodes[s_nid]["label"]
            paths_to_node[s_nid].append(f"Seed({s_label})")

        frontier: Dict[str, float] = dict(seed_nodes)
        decay = 0.58

        for hop in range(1, max_hops + 1):
            next_frontier: Dict[str, float] = defaultdict(float)
            for curr_nid, curr_score in frontier.items():
                curr_label = self.nodes.get(curr_nid, {}).get("label", curr_nid)
                for nbr_nid, rel, edge_weight in self.adj.get(curr_nid, []):
                    spread = curr_score * edge_weight * (decay ** hop)
                    if spread < 0.06:
                        continue
                    activation[nbr_nid] += spread
                    next_frontier[nbr_nid] = max(next_frontier[nbr_nid], spread)
                    visited_subgraph_nodes.add(nbr_nid)
                    nbr_label = self.nodes.get(nbr_nid, {}).get("label", nbr_nid)
                    path_str = f"{curr_label} --[{rel}]--> {nbr_label}"
                    if len(paths_to_node[nbr_nid]) < 5 and path_str not in paths_to_node[nbr_nid]:
                        paths_to_node[nbr_nid].append(path_str)
            frontier = next_frontier

        topic_graph_scores: Dict[str, float] = {}
        topic_paths: Dict[str, List[str]] = {}
        for nid in self.nodes:
            if not nid.startswith("topic:"):
                continue
            t_id = nid.split("topic:", 1)[1]
            bfs_val = activation.get(nid, 0.0)
            ppr_val = ppr_scores.get(nid, 0.0) * 15.0
            entity_bonus = sum(
                (activation.get(ent, 0.0) * 0.25 + ppr_scores.get(ent, 0.0) * 3.0)
                for ent in self.topic_to_entities.get(t_id, set())
            )
            combined_g = bfs_val + ppr_val + entity_bonus
            if combined_g > 0.01:
                topic_graph_scores[t_id] = round(combined_g, 4)
                topic_paths[t_id] = paths_to_node.get(nid, [])

        sub_nodes = [
            {
                **self.nodes[nid],
                "ppr": round(ppr_scores.get(nid, 0.0), 5),
                "ppr_score": round(ppr_scores.get(nid, 0.0), 5),
            }
            for nid in visited_subgraph_nodes
            if nid in self.nodes
        ]
        sub_edges = [
            e
            for e in self.edges
            if e["source"] in visited_subgraph_nodes and e["target"] in visited_subgraph_nodes
        ]

        subgraph = {
            "seed_entities": [self.nodes[k]["label"] for k in seed_nodes if k in self.nodes],
            "nodes": sub_nodes[:80],
            "edges": sub_edges[:160],
            "total_graph_nodes": len(self.nodes),
            "total_graph_edges": len(self.edges),
        }
        return topic_graph_scores, topic_paths, subgraph

    def get_full_graph_snapshot(self) -> Dict[str, Any]:
        """Return full knowledge graph summary, degree centrality, and node/edge lists."""
        counts_by_type: Dict[str, int] = defaultdict(int)
        enriched_nodes: List[Dict[str, Any]] = []
        for nid, n in self.nodes.items():
            counts_by_type[n.get("type", "unknown")] += 1
            degree = len(self.adj.get(nid, []))
            enriched_nodes.append({**n, "degree": degree})
        enriched_nodes.sort(key=lambda x: x.get("degree", 0), reverse=True)
        return {
            "nodes": enriched_nodes,
            "edges": self.edges,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "by_type": dict(counts_by_type),
            },
        }


class CyberspaceBoardEngine:
    """
    Production Engine for the TinCan Cyberspace Discussion Board,
    BM25 + GraphRAG hybrid search, and the @verifier-agent identity verification system.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        account_registry: Optional[Any] = None,
        ai_router: Optional[Any] = None,
        tincan_relay: Optional[Any] = None,
        webrtc_relay: Optional[Any] = None,
        seed: bool = True,
        enable_s3_sync: bool = True,
    ) -> None:
        self._lock = threading.RLock()
        if db_path is None:
            data_dir = (
                os.environ.get("TINCAN_DATA_DIR")
                or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
                or os.path.dirname(os.path.abspath(__file__))
            )
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "cyberspace_board.db")
        self.db_path = db_path
        self.account_registry = account_registry
        self.ai_router = ai_router
        self.tincan_relay = tincan_relay
        self.webrtc_relay = webrtc_relay
        self.enable_s3_sync = enable_s3_sync and (db_path != ":memory:") and ("/tmp" not in str(db_path)) and ("/var/folders" not in str(db_path))

        self.bm25 = BM25Retriever(k1=1.5, b=0.75)
        self.graphrag = CyberspaceGraphRAG()

        self._init_db()
        if self.enable_s3_sync:
            self._restore_from_s3_if_empty()
        if seed:
            self._seed_initial_knowledge_base()
        self._rebuild_indices()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cyberspace_topics (
                    topic_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    category TEXT DEFAULT 'cyberspace',
                    author_peer_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    author_verified INTEGER DEFAULT 1,
                    pinned INTEGER DEFAULT 0,
                    locked INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0,
                    accepted_post_id TEXT DEFAULT '',
                    upvotes INTEGER DEFAULT 1,
                    downvotes INTEGER DEFAULT 0,
                    score INTEGER DEFAULT 1,
                    view_count INTEGER DEFAULT 1,
                    tags_json TEXT DEFAULT '[]',
                    user_mentions_json TEXT DEFAULT '[]',
                    agent_mentions_json TEXT DEFAULT '[]',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            cursor.execute("PRAGMA table_info(cyberspace_topics)")
            t_cols = {col[1] for col in cursor.fetchall()}
            for col_name, col_def in [
                ("pinned", "INTEGER DEFAULT 0"),
                ("locked", "INTEGER DEFAULT 0"),
                ("resolved", "INTEGER DEFAULT 0"),
                ("accepted_post_id", "TEXT DEFAULT ''"),
                ("upvotes", "INTEGER DEFAULT 1"),
                ("downvotes", "INTEGER DEFAULT 0"),
                ("score", "INTEGER DEFAULT 1"),
                ("view_count", "INTEGER DEFAULT 1"),
            ]:
                if col_name not in t_cols:
                    cursor.execute(f"ALTER TABLE cyberspace_topics ADD COLUMN {col_name} {col_def}")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cyberspace_posts (
                    post_id TEXT PRIMARY KEY,
                    topic_id TEXT NOT NULL,
                    parent_post_id TEXT DEFAULT '',
                    author_peer_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    is_agent INTEGER DEFAULT 0,
                    author_verified INTEGER DEFAULT 1,
                    body TEXT NOT NULL,
                    upvotes INTEGER DEFAULT 1,
                    downvotes INTEGER DEFAULT 0,
                    score INTEGER DEFAULT 1,
                    is_accepted_solution INTEGER DEFAULT 0,
                    user_mentions_json TEXT DEFAULT '[]',
                    agent_mentions_json TEXT DEFAULT '[]',
                    hashtags_json TEXT DEFAULT '[]',
                    created_at REAL NOT NULL,
                    updated_at REAL DEFAULT 0.0,
                    FOREIGN KEY(topic_id) REFERENCES cyberspace_topics(topic_id)
                )
                """
            )
            cursor.execute("PRAGMA table_info(cyberspace_posts)")
            p_cols = {col[1] for col in cursor.fetchall()}
            for col_name, col_def in [
                ("upvotes", "INTEGER DEFAULT 1"),
                ("downvotes", "INTEGER DEFAULT 0"),
                ("score", "INTEGER DEFAULT 1"),
                ("is_accepted_solution", "INTEGER DEFAULT 0"),
                ("updated_at", "REAL DEFAULT 0.0"),
            ]:
                if col_name not in p_cols:
                    cursor.execute(f"ALTER TABLE cyberspace_posts ADD COLUMN {col_name} {col_def}")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cyberspace_votes (
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    peer_id TEXT NOT NULL,
                    vote_val INTEGER NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (target_type, target_id, peer_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS verification_forms (
                    request_id TEXT PRIMARY KEY,
                    peer_id TEXT NOT NULL,
                    target_username TEXT DEFAULT '',
                    challenge_code TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    sent_by TEXT DEFAULT '@verifier-agent',
                    reason TEXT DEFAULT '',
                    form_schema_json TEXT NOT NULL,
                    submitted_data_json TEXT DEFAULT '{}',
                    attestation_hash TEXT DEFAULT '',
                    sent_at REAL NOT NULL,
                    completed_at REAL DEFAULT 0.0
                )
                """
            )
            cursor.execute("PRAGMA table_info(verification_forms)")
            v_cols = {col[1] for col in cursor.fetchall()}
            if "challenge_code" not in v_cols:
                cursor.execute("ALTER TABLE verification_forms ADD COLUMN challenge_code TEXT DEFAULT ''")

            conn.commit()

    def _sync_to_s3_async(self) -> None:
        """Persist full Cyberspace Discussion Board state to Railway S3 in background."""
        if not self.enable_s3_sync:
            return

        def _upload():
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM cyberspace_topics")
                    topics = [dict(r) for r in cur.fetchall()]
                    cur.execute("SELECT * FROM cyberspace_posts")
                    posts = [dict(r) for r in cur.fetchall()]
                    cur.execute("SELECT * FROM cyberspace_votes")
                    votes = [dict(r) for r in cur.fetchall()]
                    cur.execute("SELECT * FROM verification_forms")
                    forms = [dict(r) for r in cur.fetchall()]
                payload = {
                    "version": "2.3.0",
                    "updated_at": time.time(),
                    "topics": topics,
                    "posts": posts,
                    "votes": votes,
                    "verification_forms": forms,
                }
                s3_put_json(payload, S3_BOARD_STATE_KEY)
            except Exception:
                pass

        threading.Thread(target=_upload, daemon=True).start()

    def _restore_from_s3_if_empty(self) -> None:
        """Restore persisted Cyberspace Board state from Railway S3 if local SQLite is empty."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cyberspace_topics")
                if cursor.fetchone()[0] > 0:
                    return

            data = s3_get_json(S3_BOARD_STATE_KEY)
            if not data or not isinstance(data, dict):
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for t in data.get("topics", []):
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO cyberspace_topics (
                            topic_id, title, body, category, author_peer_id, author_username,
                            author_verified, pinned, locked, resolved, accepted_post_id,
                            upvotes, downvotes, score, view_count, tags_json,
                            user_mentions_json, agent_mentions_json, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            t["topic_id"], t["title"], t["body"], t.get("category", "cyberspace"),
                            t["author_peer_id"], t["author_username"], t.get("author_verified", 1),
                            t.get("pinned", 0), t.get("locked", 0), t.get("resolved", 0),
                            t.get("accepted_post_id", ""), t.get("upvotes", 1), t.get("downvotes", 0),
                            t.get("score", 1), t.get("view_count", 1), t.get("tags_json", "[]"),
                            t.get("user_mentions_json", "[]"), t.get("agent_mentions_json", "[]"),
                            t["created_at"], t["updated_at"],
                        ),
                    )
                for p in data.get("posts", []):
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO cyberspace_posts (
                            post_id, topic_id, parent_post_id, author_peer_id, author_username,
                            is_agent, author_verified, body, upvotes, downvotes, score,
                            is_accepted_solution, user_mentions_json, agent_mentions_json,
                            hashtags_json, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            p["post_id"], p["topic_id"], p.get("parent_post_id", ""),
                            p["author_peer_id"], p["author_username"], p.get("is_agent", 0),
                            p.get("author_verified", 1), p["body"], p.get("upvotes", 1),
                            p.get("downvotes", 0), p.get("score", 1), p.get("is_accepted_solution", 0),
                            p.get("user_mentions_json", "[]"), p.get("agent_mentions_json", "[]"),
                            p.get("hashtags_json", "[]"), p["created_at"], p.get("updated_at", p["created_at"]),
                        ),
                    )
                for v in data.get("votes", []):
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO cyberspace_votes (target_type, target_id, peer_id, vote_val, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (v["target_type"], v["target_id"], v["peer_id"], v["vote_val"], v["updated_at"]),
                    )
                for f in data.get("verification_forms", []):
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO verification_forms (
                            request_id, peer_id, target_username, challenge_code, status,
                            sent_by, reason, form_schema_json, submitted_data_json,
                            attestation_hash, sent_at, completed_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f["request_id"], f["peer_id"], f.get("target_username", ""),
                            f.get("challenge_code", ""), f.get("status", "pending"),
                            f.get("sent_by", "@verifier-agent"), f.get("reason", ""),
                            f.get("form_schema_json", "{}"), f.get("submitted_data_json", "{}"),
                            f.get("attestation_hash", ""), f["sent_at"], f.get("completed_at", 0.0),
                        ),
                    )
                conn.commit()
        except Exception:
            pass

    def _broadcast_board_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcast live board mutations over WebRTC signaling bus so connected browsers auto-update."""
        if self.webrtc_relay is not None:
            try:
                self.webrtc_relay.exchange_signal(
                    sender_id="cyberspace-board",
                    receiver_id="*",
                    signal_type="board_event",
                    sdp_or_candidate={"event": event_type, **payload},
                    room="main",
                )
            except Exception:
                pass

    def _seed_initial_knowledge_base(self) -> None:
        """Seed foundational Cyberspace Knowledge Base topics if database is empty."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cyberspace_topics")
            if cursor.fetchone()[0] > 0:
                return

        now = time.time()
        seed_topics = [
            {
                "topic_id": "topic-cyberspace-graphrag",
                "title": "TinCan Cyberspace Knowledge Base: Hybrid Okapi BM25 + Multi-Hop GraphRAG",
                "body": (
                    "Welcome to the TinCan Cyberspace Discussion Board! Tag yourself (@alejandro), "
                    "tag collaborators (@harper), and summon AI agents (@gemini-brain @claude-brain @openai-brain) "
                    "to co-build a persistent knowledge graph in #cyberspace with #graphrag and #bm25 retrieval."
                ),
                "category": "graphrag",
                "author_peer_id": "peer-primary-mac",
                "author_username": "alejandro",
                "pinned": 1,
                "upvotes": 7,
                "score": 7,
                "tags": ["cyberspace", "graphrag", "bm25", "knowledge-base", "mesh-os"],
                "created_at": now - 3600,
                "replies": [
                    {
                        "post_id": "post-seed-01",
                        "author_peer_id": "agent:gemini-brain",
                        "author_username": "gemini-brain",
                        "is_agent": 1,
                        "upvotes": 5,
                        "score": 5,
                        "body": (
                            "🤖 [@gemini-brain]: Indexed #cyberspace architecture by @alejandro. "
                            "Every topic, nested reply, @username mention, @agent invocation, and #tag is mapped into "
                            "our Personalized PageRank (alpha=0.85) property graph alongside field-weighted Okapi #bm25 (k1=1.5, b=0.75)."
                        ),
                        "created_at": now - 3500,
                    },
                    {
                        "post_id": "post-seed-02",
                        "author_peer_id": "peer-secondary-node",
                        "author_username": "harper",
                        "is_agent": 0,
                        "upvotes": 4,
                        "score": 4,
                        "body": (
                            "Checking in as @harper with @alejandro! How does @openai-brain combine exact #bm25 lexical IDF "
                            "with 2-hop #graphrag entity paths when searching technical #ed25519 and #webrtc threads?"
                        ),
                        "created_at": now - 3400,
                    },
                    {
                        "post_id": "post-seed-03",
                        "parent_post_id": "post-seed-02",
                        "author_peer_id": "agent:openai-brain",
                        "author_username": "openai-brain",
                        "is_agent": 1,
                        "is_accepted_solution": 1,
                        "upvotes": 6,
                        "score": 6,
                        "body": (
                            "🤖 [@openai-brain]: Great question @harper and @alejandro! Okapi #bm25 scores rare technical "
                            "identifiers like #ed25519 and #webrtc via log-IDF saturation, while #graphrag spreads activation "
                            "across shared @username and @agent edges so structurally related threads surface even without exact keyword overlap."
                        ),
                        "created_at": now - 3350,
                    },
                ],
            },
            {
                "topic_id": "topic-identity-verification",
                "title": "Mandatory Cyberspace Identity Verification & @verifier-agent Attestation",
                "body": (
                    "To maintain a trusted, sybil-resistant knowledge base, @verifier-agent dispatches an interactive "
                    "#verification form (Full Legal Name, @username handle, Email, Phone Number, Role, Bio, and Cryptographic Challenge) "
                    "to verify participants before or during #cyberspace collaboration with @alejandro."
                ),
                "category": "security",
                "author_peer_id": "agent:verifier-agent",
                "author_username": "verifier-agent",
                "pinned": 1,
                "upvotes": 6,
                "score": 6,
                "tags": ["verification", "security", "zero-knowledge", "identity", "cyberspace"],
                "created_at": now - 2400,
                "replies": [
                    {
                        "post_id": "post-seed-04",
                        "author_peer_id": "agent:claude-brain",
                        "author_username": "claude-brain",
                        "is_agent": 1,
                        "upvotes": 4,
                        "score": 4,
                        "body": (
                            "🤖 [@claude-brain]: Verified @verifier-agent workflow. Binding unique @username handles to "
                            "#ed25519 peer identities and SHA-256 attestation hashes guarantees accountable #cyberspace authorship."
                        ),
                        "created_at": now - 2300,
                    }
                ],
            },
            {
                "topic_id": "topic-federated-mesh-webrtc",
                "title": "Sub-80ms WebRTC Media & CRDT Gossip Synchronization Across Nodes",
                "body": (
                    "Benchmarking low-latency #webrtc screensharing and #crdt state sync between @alejandro on Mac Studio "
                    "and @harper on Collaborator Node with @grok-brain monitoring UDP packet flights in #mesh-os."
                ),
                "category": "architecture",
                "author_peer_id": "peer-primary-mac",
                "author_username": "alejandro",
                "pinned": 0,
                "upvotes": 5,
                "score": 5,
                "tags": ["webrtc", "crdt", "mesh-os", "telemetry", "architecture"],
                "created_at": now - 1800,
                "replies": [
                    {
                        "post_id": "post-seed-05",
                        "author_peer_id": "agent:grok-brain",
                        "author_username": "grok-brain",
                        "is_agent": 1,
                        "upvotes": 3,
                        "score": 3,
                        "body": (
                            "🤖 [@grok-brain]: UDP telemetry locked for @alejandro and @harper! #webrtc signaling "
                            "and #crdt state vectors are operating under 42ms RTT across the #mesh-os relay."
                        ),
                        "created_at": now - 1750,
                    }
                ],
            },
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for st in seed_topics:
                parsed = parse_cyberspace_tags(st["body"])
                merged_tags = list(dict.fromkeys(st["tags"] + parsed["hashtags"]))
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO cyberspace_topics (
                        topic_id, title, body, category, author_peer_id, author_username,
                        author_verified, pinned, locked, resolved, accepted_post_id,
                        upvotes, downvotes, score, view_count, tags_json,
                        user_mentions_json, agent_mentions_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0, ?, ?, ?, 0, ?, 12, ?, ?, ?, ?, ?)
                    """,
                    (
                        st["topic_id"],
                        st["title"],
                        st["body"],
                        st["category"],
                        st["author_peer_id"],
                        st["author_username"],
                        st.get("pinned", 0),
                        1 if st["topic_id"] == "topic-cyberspace-graphrag" else 0,
                        "post-seed-03" if st["topic_id"] == "topic-cyberspace-graphrag" else "",
                        st.get("upvotes", 1),
                        st.get("score", 1),
                        json.dumps(merged_tags),
                        json.dumps(parsed["user_mentions"]),
                        json.dumps(parsed["agent_mentions"]),
                        st["created_at"],
                        st["created_at"],
                    ),
                )
                for rep in st.get("replies", []):
                    r_parsed = parse_cyberspace_tags(rep["body"])
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO cyberspace_posts (
                            post_id, topic_id, parent_post_id, author_peer_id, author_username,
                            is_agent, author_verified, body, upvotes, downvotes, score,
                            is_accepted_solution, user_mentions_json, agent_mentions_json,
                            hashtags_json, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rep["post_id"],
                            st["topic_id"],
                            rep.get("parent_post_id", ""),
                            rep["author_peer_id"],
                            rep["author_username"],
                            rep["is_agent"],
                            rep["body"],
                            rep.get("upvotes", 1),
                            rep.get("score", 1),
                            rep.get("is_accepted_solution", 0),
                            json.dumps(r_parsed["user_mentions"]),
                            json.dumps(r_parsed["agent_mentions"]),
                            json.dumps(r_parsed["hashtags"]),
                            rep["created_at"],
                            rep["created_at"],
                        ),
                    )
            conn.commit()

    def _load_all_topics_from_db(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cyberspace_topics ORDER BY pinned DESC, updated_at DESC")
            topic_rows = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM cyberspace_posts ORDER BY created_at ASC")
            post_rows = [dict(r) for r in cursor.fetchall()]

        posts_by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for p in post_rows:
            posts_by_topic[p["topic_id"]].append(
                {
                    "post_id": p["post_id"],
                    "topic_id": p["topic_id"],
                    "parent_post_id": p.get("parent_post_id") or "",
                    "author_peer_id": p["author_peer_id"],
                    "author_username": p["author_username"],
                    "is_agent": bool(p["is_agent"]),
                    "author_verified": bool(p["author_verified"]),
                    "body": p["body"],
                    "upvotes": int(p.get("upvotes") or 0),
                    "downvotes": int(p.get("downvotes") or 0),
                    "score": int(p.get("score") or 0),
                    "is_accepted_solution": bool(p.get("is_accepted_solution")),
                    "is_accepted": bool(p.get("is_accepted_solution")),
                    "user_mentions": json.loads(p.get("user_mentions_json") or "[]"),
                    "agent_mentions": json.loads(p.get("agent_mentions_json") or "[]"),
                    "hashtags": json.loads(p.get("hashtags_json") or "[]"),
                    "created_at": p["created_at"],
                    "updated_at": p.get("updated_at") or p["created_at"],
                }
            )

        topics: List[Dict[str, Any]] = []
        for t in topic_rows:
            t_id = t["topic_id"]
            t_posts = posts_by_topic.get(t_id, [])
            tags = json.loads(t.get("tags_json") or "[]")
            user_mentions = json.loads(t.get("user_mentions_json") or "[]")
            agent_mentions = json.loads(t.get("agent_mentions_json") or "[]")

            all_users = list(dict.fromkeys(user_mentions + [u for p in t_posts for u in p["user_mentions"]]))
            all_agents = list(dict.fromkeys(agent_mentions + [a for p in t_posts for a in p["agent_mentions"]]))
            all_tags = list(dict.fromkeys(tags + [h for p in t_posts for h in p["hashtags"]]))

            topics.append(
                {
                    "topic_id": t_id,
                    "title": t["title"],
                    "body": t["body"],
                    "category": t["category"],
                    "author_peer_id": t["author_peer_id"],
                    "author_username": t["author_username"],
                    "author_verified": bool(t["author_verified"]),
                    "pinned": bool(t.get("pinned")),
                    "locked": bool(t.get("locked")),
                    "resolved": bool(t.get("resolved")),
                    "accepted_post_id": t.get("accepted_post_id") or "",
                    "upvotes": int(t.get("upvotes") or 0),
                    "downvotes": int(t.get("downvotes") or 0),
                    "score": int(t.get("score") or 0),
                    "view_count": int(t.get("view_count") or 1),
                    "views": int(t.get("view_count") or 1),
                    "tags": all_tags,
                    "user_mentions": all_users,
                    "agent_mentions": all_agents,
                    "posts": t_posts,
                    "reply_count": len(t_posts),
                    "created_at": t["created_at"],
                    "updated_at": t["updated_at"],
                }
            )
        return topics

    def _rebuild_indices(self) -> None:
        """Synchronize in-memory BM25 inverted index and GraphRAG property graph."""
        with self._lock:
            topics = self._load_all_topics_from_db()
            self.bm25.index_documents(topics)
            self.graphrag.build_graph(topics)

    # =========================================================================
    # Identity Verification Agent (@verifier-agent)
    # =========================================================================

    def is_peer_verified(self, peer_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if a peer has a verified identity in Verification Forms or PeerAccountRegistry."""
        peer_id = (peer_id or "").strip()
        if not peer_id:
            return False, None
        if peer_id.startswith("agent:"):
            ag_name = peer_id.split(":", 1)[1]
            return True, {"peer_id": peer_id, "username": ag_name, "verified": True, "verified_by": "@verifier-agent"}

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM verification_forms WHERE peer_id = ? AND status = 'completed' ORDER BY completed_at DESC LIMIT 1",
                (peer_id,),
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row["submitted_data_json"] or "{}")
                data["attestation_hash"] = row["attestation_hash"]
                data["challenge_code"] = row["challenge_code"]
                data["verified"] = True
                return True, data

        if self.account_registry is not None:
            acc = self.account_registry.get_account_by_peer(peer_id)
            if acc and acc.get("username") and acc.get("email") and acc.get("consent_pii"):
                if not str(acc.get("email", "")).endswith("@mesh.local"):
                    att_hash = hashlib.sha256(f"{peer_id}:{acc['username']}:{acc['email']}".encode("utf-8")).hexdigest()[:24]
                    return True, {
                        **acc,
                        "verified": True,
                        "verified_by": "@verifier-agent",
                        "attestation_hash": att_hash,
                        "badge": "✅ Verified Cyberspace Citizen",
                    }

        return False, None

    def dispatch_verification_form(
        self,
        peer_id: str,
        target_username: str = "",
        reason: str = "Mandatory Cyberspace Identity Verification",
        dispatched_by_peer: str = "@verifier-agent",
    ) -> Dict[str, Any]:
        """
        Have @verifier-agent send a structured identity verification form with a cryptographic
        challenge code to a peer or @username.
        """
        peer_id = (peer_id or "anonymous-peer").strip()
        target_username = (target_username or "").strip().lstrip("@").lower()
        req_id = f"vrf-{uuid.uuid4().hex[:10]}"
        challenge_code = f"CYBER-{uuid.uuid4().hex[:6].upper()}"
        now = time.time()

        form_schema = {
            "form_id": req_id,
            "challenge_code": challenge_code,
            "title": "TinCan Cyberspace Identity Verification Form",
            "dispatched_by": "@verifier-agent",
            "requested_by": dispatched_by_peer,
            "peer_id": peer_id,
            "target_username": target_username,
            "reason": reason,
            "instructions": (
                f"🛡️ Hello from @verifier-agent! Please complete and sign this identity verification form "
                f"(Challenge Code: {challenge_code}) to verify who you are and unlock full Cyberspace Knowledge Base privileges."
            ),
            "fields": [
                {"name": "full_name", "label": "Full Legal / Real Name", "type": "text", "required": True},
                {"name": "username", "label": "Cyberspace Username (@handle)", "type": "text", "required": True, "default": target_username},
                {"name": "email", "label": "Verified Contact Email", "type": "email", "required": True},
                {"name": "phone_number", "label": "Phone Number (SMS/2FA)", "type": "tel", "required": True},
                {"name": "role", "label": "Institution / Role", "type": "select", "required": True, "default": "FAU Graduate School / Academic"},
                {"name": "bio", "label": "Cyberspace Knowledge Domain / Research Bio", "type": "text", "required": False},
                {"name": "challenge_code", "label": "Agent Challenge Code", "type": "text", "required": True, "default": challenge_code},
                {"name": "consent_pii", "label": "I attest my identity and consent to cryptographic verification", "type": "checkbox", "required": True},
            ],
        }

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO verification_forms (
                        request_id, peer_id, target_username, challenge_code, status, sent_by,
                        reason, form_schema_json, submitted_data_json, attestation_hash, sent_at
                    )
                    VALUES (?, ?, ?, ?, 'pending', '@verifier-agent', ?, ?, '{}', '', ?)
                    """,
                    (req_id, peer_id, target_username, challenge_code, reason, json.dumps(form_schema), now),
                )
                conn.commit()
            self._sync_to_s3_async()

        if self.webrtc_relay is not None:
            try:
                self.webrtc_relay.exchange_signal(
                    sender_id="@verifier-agent",
                    receiver_id=peer_id,
                    signal_type="verification_form",
                    sdp_or_candidate=form_schema,
                    room="main",
                )
                if target_username:
                    self.webrtc_relay.exchange_signal(
                        sender_id="@verifier-agent",
                        receiver_id="*",
                        signal_type="verification_form_broadcast",
                        sdp_or_candidate={**form_schema, "target_username": target_username},
                        room="main",
                    )
            except Exception:
                pass

        if self.tincan_relay is not None:
            try:
                self.tincan_relay.send(
                    {
                        "from": "@verifier-agent",
                        "to": peer_id,
                        "ciphertext": json.dumps(
                            {
                                "type": "VERIFICATION_FORM_DISPATCH",
                                "agent": "@verifier-agent",
                                "form": form_schema,
                            }
                        ),
                    }
                )
            except Exception:
                pass

        return {
            "status": "dispatched",
            "agent": "@verifier-agent",
            "request_id": req_id,
            "challenge_code": challenge_code,
            "peer_id": peer_id,
            "target_username": target_username,
            "reason": reason,
            "form": form_schema,
            "sent_at": now,
        }

    def submit_verification_form(
        self,
        peer_id: str,
        full_name: str,
        username: str,
        email: str,
        phone_number: str,
        role: str = "FAU Graduate School / Academic",
        bio: str = "",
        consent_pii: bool = True,
        request_id: Optional[str] = None,
        challenge_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process and verify a user's submitted identity form via @verifier-agent.
        Validates fields, checks @username uniqueness across peers, syncs with PeerAccountRegistry,
        and issues a SHA-256 cryptographic attestation certificate.
        """
        peer_id = (peer_id or "").strip()
        full_name = (full_name or "").strip()
        username = re.sub(r"[^a-zA-Z0-9_\-]", "", (username or "").strip().lstrip("@").lower())
        email = (email or "").strip().lower()
        phone_number = (phone_number or "").strip()
        role = (role or "FAU Graduate School / Academic").strip()
        bio = (bio or "").strip()

        if not peer_id:
            raise ValueError("peer_id is required for identity verification")
        if len(full_name) < 2:
            raise ValueError("Full Legal Name is required (minimum 2 characters)")
        if len(username) < 2:
            raise ValueError("Valid @username handle is required (minimum 2 alphanumeric characters)")
        if username in KNOWN_AI_AGENTS:
            raise ValueError(f"@{username} is a reserved AI agent handle")
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ValueError(f"Invalid email address: {email}")
        cleaned_phone = re.sub(r"[^\d+]", "", phone_number)
        if len(re.sub(r"\D", "", cleaned_phone)) < 10:
            raise ValueError("Valid phone number (minimum 10 digits) is required")
        if not consent_pii:
            raise ValueError("Identity attestation & PII consent is required by @verifier-agent")

        now = time.time()
        resolved_challenge = (challenge_code or "").strip() or f"CYBER-{uuid.uuid4().hex[:6].upper()}"
        attestation_payload = f"{peer_id}:{username}:{full_name}:{email}:{cleaned_phone}:{resolved_challenge}:{int(now)}"
        attestation_hash = hashlib.sha256(attestation_payload.encode("utf-8")).hexdigest()[:24]

        account_record = None
        if self.account_registry is not None:
            account_record = self.account_registry.register_account(
                peer_id=peer_id,
                full_name=full_name,
                phone_number=phone_number,
                email=email,
                username=username,
                role=role,
                consent_pii=True,
            )

        submitted_data = {
            "peer_id": peer_id,
            "full_name": full_name,
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "role": role,
            "bio": bio or f"{role} · Cyberspace Builder",
            "challenge_code": resolved_challenge,
            "consent_pii": True,
            "verified_by": "@verifier-agent",
            "attestation_hash": attestation_hash,
            "verified_at": now,
            "badge": "✅ Verified Cyberspace Citizen",
        }

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if request_id:
                    cursor.execute(
                        """
                        UPDATE verification_forms
                        SET status = 'completed',
                            peer_id = ?,
                            target_username = ?,
                            submitted_data_json = ?,
                            attestation_hash = ?,
                            completed_at = ?
                        WHERE request_id = ?
                        """,
                        (peer_id, username, json.dumps(submitted_data), attestation_hash, now, request_id),
                    )
                    if cursor.rowcount == 0:
                        cursor.execute(
                            """
                            INSERT INTO verification_forms (
                                request_id, peer_id, target_username, challenge_code, status, sent_by,
                                reason, form_schema_json, submitted_data_json, attestation_hash, sent_at, completed_at
                            )
                            VALUES (?, ?, ?, ?, 'completed', '@verifier-agent', 'Form Submission', '{}', ?, ?, ?, ?)
                            """,
                            (request_id, peer_id, username, resolved_challenge, json.dumps(submitted_data), attestation_hash, now, now),
                        )
                else:
                    req_id = f"vrf-{uuid.uuid4().hex[:10]}"
                    cursor.execute(
                        """
                        INSERT INTO verification_forms (
                            request_id, peer_id, target_username, challenge_code, status, sent_by,
                            reason, form_schema_json, submitted_data_json, attestation_hash, sent_at, completed_at
                        )
                        VALUES (?, ?, ?, ?, 'completed', '@verifier-agent', 'Direct Form Submission', '{}', ?, ?, ?, ?)
                        """,
                        (req_id, peer_id, username, resolved_challenge, json.dumps(submitted_data), attestation_hash, now, now),
                    )

                cursor.execute(
                    """
                    UPDATE verification_forms
                    SET status = 'completed',
                        submitted_data_json = ?,
                        attestation_hash = ?,
                        completed_at = ?
                    WHERE (peer_id = ? OR target_username = ?) AND status = 'pending'
                    """,
                    (json.dumps(submitted_data), attestation_hash, now, peer_id, username),
                )
                # Also mark any topics/posts by this peer_id or username as verified
                cursor.execute(
                    "UPDATE cyberspace_topics SET author_verified = 1 WHERE author_peer_id = ? OR author_username = ?",
                    (peer_id, username),
                )
                cursor.execute(
                    "UPDATE cyberspace_posts SET author_verified = 1 WHERE author_peer_id = ? OR author_username = ?",
                    (peer_id, username),
                )
                conn.commit()

            self._rebuild_indices()
            self._sync_to_s3_async()

        self._broadcast_board_event("citizen_verified", {"username": f"@{username}", "peer_id": peer_id, "attestation_hash": attestation_hash})

        return {
            "status": "verified",
            "verified": True,
            "agent": "@verifier-agent",
            "peer_id": peer_id,
            "username": f"@{username}",
            "full_name": full_name,
            "role": role,
            "bio": submitted_data["bio"],
            "challenge_code": resolved_challenge,
            "attestation_hash": attestation_hash,
            "badge": "✅ Verified Cyberspace Citizen",
            "account": account_record or submitted_data,
        }

    def get_verification_status(self, peer_id: str, username: str = "") -> Dict[str, Any]:
        """Inspect a peer's verification status and any pending form sent by @verifier-agent."""
        verified, profile = self.is_peer_verified(peer_id)
        clean_un = (username or "").strip().lstrip("@").lower()
        if not clean_un and profile and profile.get("username"):
            clean_un = str(profile["username"]).strip().lstrip("@").lower()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if clean_un:
                cursor.execute(
                    "SELECT * FROM verification_forms WHERE peer_id = ? OR target_username = ? ORDER BY sent_at DESC LIMIT 10",
                    ((peer_id or "").strip(), clean_un),
                )
            else:
                cursor.execute(
                    "SELECT * FROM verification_forms WHERE peer_id = ? ORDER BY sent_at DESC LIMIT 10",
                    ((peer_id or "").strip(),),
                )
            forms = []
            for r_row in cursor.fetchall():
                r = dict(r_row)
                forms.append(
                    {
                        "request_id": r["request_id"],
                        "peer_id": r["peer_id"],
                        "target_username": r["target_username"],
                        "challenge_code": r.get("challenge_code") or "",
                        "status": r["status"],
                        "sent_by": r["sent_by"],
                        "reason": r["reason"],
                        "form": json.loads(r["form_schema_json"] or "{}"),
                        "submitted_data": json.loads(r["submitted_data_json"] or "{}"),
                        "attestation_hash": r["attestation_hash"],
                        "sent_at": r["sent_at"],
                        "completed_at": r["completed_at"],
                    }
                )

        pending = [f for f in forms if f["status"] == "pending"]
        return {
            "peer_id": peer_id,
            "verified": verified,
            "verified_by": "@verifier-agent" if verified else None,
            "profile": profile,
            "pending_forms": pending,
            "pending_requests": pending,
            "history": forms,
        }

    def list_verifications(self) -> Dict[str, Any]:
        """Return all verified citizens and all pending verification requests for the Verification Center."""
        verified_citizens: Dict[str, Dict[str, Any]] = {}

        if self.account_registry is not None:
            for acc in self.account_registry.list_accounts():
                un = (acc.get("username") or "").strip().lstrip("@").lower()
                if not un or str(acc.get("email", "")).endswith("@mesh.local"):
                    continue
                att_hash = hashlib.sha256(f"{acc['peer_id']}:{un}:{acc['email']}".encode("utf-8")).hexdigest()[:24]
                verified_citizens[un] = {
                    "username": f"@{un}",
                    "full_name": acc.get("full_name", un),
                    "peer_id": acc.get("peer_id", ""),
                    "role": acc.get("role", "Researcher / Student"),
                    "bio": f"{acc.get('role', 'Operator')} on TinCan Mesh",
                    "verified": True,
                    "verified_by": "@verifier-agent",
                    "attestation_hash": att_hash,
                    "verified_at": acc.get("created_at", 0.0),
                    "badge": "✅ Verified Cyberspace Citizen",
                }

        pending_requests: List[Dict[str, Any]] = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM verification_forms ORDER BY sent_at DESC LIMIT 50")
            for r_row in cursor.fetchall():
                r = dict(r_row)
                if r["status"] == "completed":
                    sub = json.loads(r["submitted_data_json"] or "{}")
                    un = (sub.get("username") or r["target_username"] or "").strip().lstrip("@").lower()
                    if un:
                        verified_citizens[un] = {
                            "username": f"@{un}",
                            "full_name": sub.get("full_name", un),
                            "peer_id": r["peer_id"],
                            "role": sub.get("role", "Researcher / Student"),
                            "bio": sub.get("bio", ""),
                            "verified": True,
                            "verified_by": "@verifier-agent",
                            "challenge_code": r.get("challenge_code") or sub.get("challenge_code", ""),
                            "attestation_hash": r["attestation_hash"],
                            "verified_at": r["completed_at"] or r["sent_at"],
                            "badge": "✅ Verified Cyberspace Citizen",
                        }
                else:
                    pending_requests.append(
                        {
                            "request_id": r["request_id"],
                            "peer_id": r["peer_id"],
                            "target_username": f"@{r['target_username']}" if r["target_username"] else "unassigned",
                            "challenge_code": r.get("challenge_code") or "",
                            "status": r.get("status", "pending"),
                            "reason": r["reason"],
                            "sent_by": r["sent_by"],
                            "sent_at": r["sent_at"],
                            "form": json.loads(r["form_schema_json"] or "{}"),
                        }
                    )

        return {
            "agent": "@verifier-agent",
            "verified_count": len(verified_citizens),
            "pending_count": len(pending_requests),
            "verified_citizens": list(verified_citizens.values()),
            "pending_requests": pending_requests,
            "requests": pending_requests,
        }

    # =========================================================================
    # User & Agent Roster + Citizen Profiles
    # =========================================================================

    def get_roster_and_profiles(self) -> Dict[str, Any]:
        """Return live roster of all @users, @agents, #tags, and categories in Cyberspace."""
        verifications = self.list_verifications()
        users_map: Dict[str, Dict[str, Any]] = {
            c["username"].lstrip("@").lower(): dict(c, topics_count=0, posts_count=0, reputation=10)
            for c in verifications["verified_citizens"]
        }

        with self._lock:
            topics = self._load_all_topics_from_db()

        tag_counter: Counter = Counter()
        cat_counter: Counter = Counter()

        for t in topics:
            cat_counter[t.get("category", "cyberspace")] += 1
            for tag in t.get("tags", []):
                tag_counter[tag.lower().lstrip("#")] += 1

            t_author = (t.get("author_username") or "anonymous").lower().lstrip("@")
            if t_author not in KNOWN_AI_AGENTS:
                if t_author not in users_map:
                    users_map[t_author] = {
                        "username": f"@{t_author}",
                        "full_name": t_author.capitalize(),
                        "peer_id": t.get("author_peer_id", ""),
                        "role": "Cyberspace Contributor",
                        "bio": "Active participant in TinCan Cyberspace",
                        "verified": bool(t.get("author_verified")),
                        "verified_by": "@verifier-agent" if t.get("author_verified") else None,
                        "attestation_hash": hashlib.sha256(f"seed:{t_author}".encode("utf-8")).hexdigest()[:24] if t.get("author_verified") else "",
                        "topics_count": 0,
                        "posts_count": 0,
                        "reputation": 0,
                    }
                users_map[t_author]["topics_count"] += 1
                users_map[t_author]["reputation"] += 15 + int(t.get("score", 0)) * 5

            for p in t.get("posts", []):
                if p.get("is_agent"):
                    continue
                p_author = (p.get("author_username") or "anonymous").lower().lstrip("@")
                if p_author not in users_map:
                    users_map[p_author] = {
                        "username": f"@{p_author}",
                        "full_name": p_author.capitalize(),
                        "peer_id": p.get("author_peer_id", ""),
                        "role": "Cyberspace Contributor",
                        "bio": "Active participant in TinCan Cyberspace",
                        "verified": bool(p.get("author_verified")),
                        "verified_by": "@verifier-agent" if p.get("author_verified") else None,
                        "attestation_hash": hashlib.sha256(f"seed:{p_author}".encode("utf-8")).hexdigest()[:24] if p.get("author_verified") else "",
                        "topics_count": 0,
                        "posts_count": 0,
                        "reputation": 0,
                    }
                users_map[p_author]["posts_count"] += 1
                users_map[p_author]["reputation"] += 10 + int(p.get("score", 0)) * 3

        users_list = sorted(users_map.values(), key=lambda u: (u.get("reputation", 0), u.get("verified", False)), reverse=True)
        unique_agents = []
        seen_ag = set()
        for k, ag in KNOWN_AI_AGENTS.items():
            if k in ("claude-sonnet", "gpt-4o"):
                continue
            if k not in seen_ag:
                seen_ag.add(k)
                unique_agents.append(ag)

        return {
            "users": users_list,
            "agents": unique_agents,
            "popular_tags": [{"tag": f"#{k}", "name": k, "count": v} for k, v in tag_counter.most_common(25)],
            "categories": [
                {**c, "count": cat_counter.get(c["id"], 0)}
                for c in BOARD_CATEGORIES
            ],
        }

    def get_user_profile(self, username_or_peer: str) -> Dict[str, Any]:
        """Get a detailed Cyberspace Citizen Profile with authored topics, replies, and graph neighbors."""
        target = (username_or_peer or "").strip().lstrip("@").lower()
        roster = self.get_roster_and_profiles()
        profile = next(
            (u for u in roster["users"] if u["username"].lstrip("@").lower() == target or u.get("peer_id", "").lower() == target),
            None,
        )
        if not profile and target in KNOWN_AI_AGENTS:
            ag = KNOWN_AI_AGENTS[target]
            profile = {
                "username": f"@{target}",
                "full_name": ag["display_name"],
                "peer_id": f"agent:{target}",
                "role": "Autonomous AI Agent",
                "bio": ag["specialty"],
                "verified": True,
                "verified_by": "@verifier-agent",
                "attestation_hash": hashlib.sha256(f"agent:{target}".encode("utf-8")).hexdigest()[:24],
                "is_agent": True,
            }
        if not profile:
            profile = {
                "username": f"@{target}",
                "full_name": target,
                "peer_id": target,
                "role": "Unverified Peer",
                "bio": "Has not yet completed @verifier-agent identity verification form.",
                "verified": False,
            }

        un_clean = profile["username"].lstrip("@").lower()
        topics = self.list_topics(mentioned_user=un_clean if not profile.get("is_agent") else None, mentioned_agent=un_clean if profile.get("is_agent") else None)["topics"]
        node_key = f"agent:@{un_clean}" if profile.get("is_agent") else f"user:@{un_clean}"
        connections = [
            {
                "node": nbr,
                "label": self.graphrag.nodes.get(nbr, {}).get("label", nbr),
                "type": self.graphrag.nodes.get(nbr, {}).get("type", "entity"),
                "relation": rel,
            }
            for nbr, rel, _ in self.graphrag.adj.get(node_key, [])
        ]

        return {
            "verified": bool(profile.get("verified")),
            "profile": profile,
            "authored_count": int(profile.get("topics_count", 0)),
            "reply_count": int(profile.get("posts_count", 0)),
            "mentioned_count": len(topics),
            "authored_topics": topics[:10],
            "related_topics": topics[:15],
            "graph_connections": connections[:25],
        }

    # =========================================================================
    # Discussion Board: Topics, Nested Replies, Voting & Solutions
    # =========================================================================

    def _resolve_username(self, peer_id: str, provided_username: Optional[str] = None) -> Tuple[str, bool]:
        verified, profile = self.is_peer_verified(peer_id)
        if provided_username and provided_username.strip():
            clean = re.sub(r"[^a-zA-Z0-9_\-]", "", provided_username.strip().lstrip("@").lower())
            if clean:
                return clean, verified
        if profile and profile.get("username"):
            return str(profile["username"]).strip().lstrip("@").lower(), verified
        clean_peer = re.sub(r"[^a-zA-Z0-9_\-]", "", peer_id)[:16].lower() or "anonymous"
        return clean_peer, verified

    def _generate_agent_reply(
        self,
        agent_handle: str,
        topic_title: str,
        trigger_body: str,
        author_username: str,
        tags: List[str],
        user_mentions: List[str],
    ) -> str:
        """Synthesize an intelligent response when an AI agent (@gemini-brain, @verifier-agent, etc.) is tagged."""
        agent_key = agent_handle.lower().lstrip("@")
        agent_meta = KNOWN_AI_AGENTS.get(
            agent_key,
            {
                "alias": "gemini-brain",
                "display_name": f"AI Agent (@{agent_key})",
                "specialty": "Cyberspace knowledge synthesis",
            },
        )

        if agent_key == "verifier-agent":
            mentioned_targets = [u for u in user_mentions if u != author_username]
            if mentioned_targets:
                dispatched_ids = []
                for target_u in mentioned_targets:
                    d = self.dispatch_verification_form(
                        peer_id=f"user:{target_u}",
                        target_username=target_u,
                        reason=f"Tagged by @{author_username} in topic '{topic_title}' for identity verification",
                        dispatched_by_peer=f"@{author_username}",
                    )
                    dispatched_ids.append(f"@{target_u} (Form `{d['request_id']}`, Challenge `{d['challenge_code']}`)")
                return (
                    f"🛡️ [@verifier-agent Dispatch]: Identity verification form has been sent to {', '.join(dispatched_ids)} "
                    f"(requested by @{author_username}). They can open the **🛡️ Verify Center** tab to fill out the form and verify who they are!"
                )
            d = self.dispatch_verification_form(
                peer_id=f"user:{author_username}",
                target_username=author_username,
                reason=f"Requested verification form in '{topic_title}'",
                dispatched_by_peer=f"@{author_username}",
            )
            return (
                f"🛡️ [@verifier-agent Dispatch]: Sent Identity Verification Form `{d['request_id']}` "
                f"(Challenge Code: `{d['challenge_code']}`) to @{author_username}. Open the **🛡️ Verify Center** tab to submit and claim your attestation badge!"
            )

        # Retrieve top GraphRAG + BM25 context to ground the AI agent's reply
        search_res = self.search(f"{topic_title} {trigger_body}", mode="hybrid", top_k=3, synthesize_llm=False)
        related_snippets = []
        for r in search_res.get("results", []):
            if r.get("title") != topic_title:
                related_snippets.append(f"\"{r['title']}\" (by {r['author_username']}, score={r['score']:.2f})")

        tags_str = " ".join(f"#{t}" for t in tags[:4]) if tags else "#cyberspace #graphrag"
        users_str = " ".join(f"@{u}" for u in dict.fromkeys([author_username] + user_mentions))

        # Call live OpenRouter LLM via DynamicAIGatewayRouter if available
        if self.ai_router is not None:
            try:
                resp = self.ai_router.dispatch_completion(
                    alias=agent_meta["alias"],
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are @{agent_key} ({agent_meta['display_name']}), an autonomous AI agent on the TinCan "
                                f"Cyberspace Discussion Board. Your specialty is {agent_meta['specialty']}. "
                                f"Respond directly and insightfully in 2-4 sentences, address {users_str}, include relevant "
                                f"#hashtags ({tags_str}), and reference connected GraphRAG context if helpful: {'; '.join(related_snippets[:2]) or 'none'}."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Topic Title: {topic_title}\nPost by @{author_username}: {trigger_body}",
                        },
                    ],
                    max_tokens=220,
                )
                content = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if content and not content.startswith("[Simulated"):
                    if not content.startswith("🤖"):
                        content = f"🤖 [@{agent_key}]: {content}"
                    return content
            except Exception:
                pass

        context_note = (
            f" Connected in the Cyberspace Knowledge Graph with {', '.join(related_snippets[:2])}."
            if related_snippets
            else ""
        )
        return (
            f"🤖 [@{agent_key} Synthesis]: Acknowledged {users_str} on \"{topic_title}\". "
            f"Indexed key concepts ({tags_str}) into the TinCan Cyberspace Knowledge Graph "
            f"(specialty: {agent_meta['specialty']}).{context_note}"
        )

    def create_topic(
        self,
        peer_id: str,
        title: str,
        body: str,
        category: str = "cyberspace",
        tags: Optional[List[str]] = None,
        author_username: Optional[str] = None,
        require_verification: bool = False,
        auto_agent_reply: bool = True,
    ) -> Dict[str, Any]:
        """Create a new discussion topic in the Cyberspace Knowledge Base."""
        peer_id = (peer_id or "anonymous-peer").strip()
        title = (title or "").strip()
        body = (body or "").strip()
        category = (category or "cyberspace").strip().lower()

        if not title:
            raise ValueError("Topic title is required")
        if not body:
            raise ValueError("Topic body is required")

        username, is_verified = self._resolve_username(peer_id, author_username)

        if require_verification and not is_verified:
            dispatch = self.dispatch_verification_form(
                peer_id=peer_id,
                target_username=username,
                reason=f"Attempted to create topic '{title}' without completed identity verification",
            )
            return {
                "status": "verification_required",
                "require_verification": True,
                "agent": "@verifier-agent",
                "message": (
                    "🛡️ @verifier-agent has sent you the Identity Verification Form. "
                    "Please fill out the form to verify who you are before posting."
                ),
                "verification_dispatch": dispatch,
            }

        parsed = parse_cyberspace_tags(f"{title} {body}")
        explicit_tags = [str(t).strip().lstrip("#").lower() for t in (tags or []) if str(t).strip()]
        merged_tags = list(dict.fromkeys(explicit_tags + parsed["hashtags"] + [category]))
        user_mentions = parsed["user_mentions"]
        agent_mentions = parsed["agent_mentions"]

        topic_id = f"topic-{uuid.uuid4().hex[:10]}"
        now = time.time()

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO cyberspace_topics (
                        topic_id, title, body, category, author_peer_id, author_username,
                        author_verified, pinned, locked, resolved, accepted_post_id,
                        upvotes, downvotes, score, view_count, tags_json,
                        user_mentions_json, agent_mentions_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, '', 1, 0, 1, 1, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic_id,
                        title,
                        body,
                        category,
                        peer_id,
                        username,
                        1 if is_verified else 0,
                        json.dumps(merged_tags),
                        json.dumps(user_mentions),
                        json.dumps(agent_mentions),
                        now,
                        now,
                    ),
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO cyberspace_votes (target_type, target_id, peer_id, vote_val, updated_at) VALUES ('topic', ?, ?, 1, ?)",
                    (topic_id, peer_id, now),
                )
                conn.commit()

            self._rebuild_indices()

            if auto_agent_reply and agent_mentions:
                for agent_handle in agent_mentions[:3]:
                    reply_text = self._generate_agent_reply(
                        agent_handle=agent_handle,
                        topic_title=title,
                        trigger_body=body,
                        author_username=username,
                        tags=merged_tags,
                        user_mentions=user_mentions,
                    )
                    self.create_post(
                        topic_id=topic_id,
                        peer_id=f"agent:{agent_handle}",
                        body=reply_text,
                        author_username=agent_handle,
                        is_agent=True,
                        auto_agent_reply=False,
                    )

            self._sync_to_s3_async()
            created_topic = self.get_topic(topic_id)
            self._broadcast_board_event("topic_created", {"topic_id": topic_id, "title": title, "author": f"@{username}"})
            return created_topic

    def update_topic(
        self,
        topic_id: str,
        peer_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        pinned: Optional[bool] = None,
        locked: Optional[bool] = None,
        resolved: Optional[bool] = None,
        is_admin: bool = False,
    ) -> Dict[str, Any]:
        """Edit or moderate an existing topic (author or admin)."""
        with self._lock:
            existing = self.get_topic(topic_id)
            if not existing:
                raise ValueError(f"Topic '{topic_id}' not found")
            if not is_admin and existing["author_peer_id"] != peer_id:
                raise PermissionError("Only the topic author or an admin moderator can edit this topic")

            new_title = title.strip() if title is not None and title.strip() else existing["title"]
            new_body = body.strip() if body is not None and body.strip() else existing["body"]
            new_cat = category.strip().lower() if category is not None and category.strip() else existing["category"]
            new_pinned = int(pinned) if pinned is not None else int(existing.get("pinned", False))
            new_locked = int(locked) if locked is not None else int(existing.get("locked", False))
            new_resolved = int(resolved) if resolved is not None else int(existing.get("resolved", False))

            parsed = parse_cyberspace_tags(f"{new_title} {new_body}")
            explicit_tags = [str(t).strip().lstrip("#").lower() for t in (tags if tags is not None else existing["tags"]) if str(t).strip()]
            merged_tags = list(dict.fromkeys(explicit_tags + parsed["hashtags"] + [new_cat]))
            now = time.time()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE cyberspace_topics
                    SET title = ?, body = ?, category = ?, pinned = ?, locked = ?, resolved = ?,
                        tags_json = ?, user_mentions_json = ?, agent_mentions_json = ?, updated_at = ?
                    WHERE topic_id = ?
                    """,
                    (
                        new_title, new_body, new_cat, new_pinned, new_locked, new_resolved,
                        json.dumps(merged_tags), json.dumps(parsed["user_mentions"]),
                        json.dumps(parsed["agent_mentions"]), now, topic_id,
                    ),
                )
                conn.commit()

            self._rebuild_indices()
            self._sync_to_s3_async()
            return self.get_topic(topic_id)

    def delete_topic(self, topic_id: str, peer_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """Delete a topic and its posts (author or admin)."""
        with self._lock:
            existing = self.get_topic(topic_id)
            if not existing:
                raise ValueError(f"Topic '{topic_id}' not found")
            if not is_admin and existing["author_peer_id"] != peer_id:
                raise PermissionError("Only the topic author or an admin moderator can delete this topic")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cyberspace_posts WHERE topic_id = ?", (topic_id,))
                cursor.execute("DELETE FROM cyberspace_votes WHERE target_type = 'topic' AND target_id = ?", (topic_id,))
                cursor.execute("DELETE FROM cyberspace_topics WHERE topic_id = ?", (topic_id,))
                conn.commit()

            self._rebuild_indices()
            self._sync_to_s3_async()
            self._broadcast_board_event("topic_deleted", {"topic_id": topic_id})
            return {"status": "deleted", "topic_id": topic_id}

    def create_post(
        self,
        topic_id: str,
        peer_id: str,
        body: str,
        author_username: Optional[str] = None,
        parent_post_id: str = "",
        is_agent: bool = False,
        require_verification: bool = False,
        auto_agent_reply: bool = True,
    ) -> Dict[str, Any]:
        """Add a reply/post (or nested reply) to an existing topic."""
        topic_id = (topic_id or "").strip()
        peer_id = (peer_id or "anonymous-peer").strip()
        body = (body or "").strip()
        if not topic_id:
            raise ValueError("topic_id is required")
        if not body:
            raise ValueError("Post body is required")

        existing_topic = self.get_topic(topic_id)
        if not existing_topic:
            raise ValueError(f"Topic '{topic_id}' not found")
        if existing_topic.get("locked") and not is_agent:
            raise ValueError("This topic is locked by a moderator")

        username, is_verified = self._resolve_username(peer_id, author_username)
        if is_agent:
            is_verified = True

        if require_verification and not is_verified:
            dispatch = self.dispatch_verification_form(
                peer_id=peer_id,
                target_username=username,
                reason=f"Attempted to reply in topic '{existing_topic['title']}' without verification",
            )
            return {
                "status": "verification_required",
                "require_verification": True,
                "agent": "@verifier-agent",
                "message": (
                    "🛡️ @verifier-agent has sent you the Identity Verification Form. "
                    "Please complete verification to post in this thread."
                ),
                "verification_dispatch": dispatch,
            }

        parsed = parse_cyberspace_tags(body)
        post_id = f"post-{uuid.uuid4().hex[:10]}"
        now = time.time()

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO cyberspace_posts (
                        post_id, topic_id, parent_post_id, author_peer_id, author_username,
                        is_agent, author_verified, body, upvotes, downvotes, score,
                        is_accepted_solution, user_mentions_json, agent_mentions_json,
                        hashtags_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 1, 0, ?, ?, ?, ?, ?)
                    """,
                    (
                        post_id,
                        topic_id,
                        parent_post_id or "",
                        peer_id,
                        username,
                        1 if is_agent else 0,
                        1 if is_verified else 0,
                        body,
                        json.dumps(parsed["user_mentions"]),
                        json.dumps(parsed["agent_mentions"]),
                        json.dumps(parsed["hashtags"]),
                        now,
                        now,
                    ),
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO cyberspace_votes (target_type, target_id, peer_id, vote_val, updated_at) VALUES ('post', ?, ?, 1, ?)",
                    (post_id, peer_id, now),
                )
                cursor.execute(
                    "UPDATE cyberspace_topics SET updated_at = ? WHERE topic_id = ?",
                    (now, topic_id),
                )
                conn.commit()

            self._rebuild_indices()

            agent_replies: List[Dict[str, Any]] = []
            if auto_agent_reply and not is_agent and parsed["agent_mentions"]:
                for agent_handle in parsed["agent_mentions"][:2]:
                    reply_text = self._generate_agent_reply(
                        agent_handle=agent_handle,
                        topic_title=existing_topic["title"],
                        trigger_body=body,
                        author_username=username,
                        tags=existing_topic.get("tags", []) + parsed["hashtags"],
                        user_mentions=parsed["user_mentions"],
                    )
                    ag_post = self.create_post(
                        topic_id=topic_id,
                        peer_id=f"agent:{agent_handle}",
                        body=reply_text,
                        author_username=agent_handle,
                        parent_post_id=post_id,
                        is_agent=True,
                        auto_agent_reply=False,
                    )
                    agent_replies.append(ag_post)

            self._sync_to_s3_async()
            updated_topic = self.get_topic(topic_id)
            self._broadcast_board_event("post_created", {"topic_id": topic_id, "post_id": post_id, "author": f"@{username}"})
            return {
                "status": "posted",
                "post_id": post_id,
                "topic_id": topic_id,
                "parent_post_id": parent_post_id or "",
                "author_username": f"@{username}",
                "author_verified": is_verified,
                "user_mentions": parsed["user_mentions"],
                "agent_mentions": parsed["agent_mentions"],
                "hashtags": parsed["hashtags"],
                "agent_replies": agent_replies,
                "topic": updated_topic,
            }

    def delete_post(self, post_id: str, peer_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """Delete a reply/post from a topic (author or admin)."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cyberspace_posts WHERE post_id = ?", (post_id,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Post '{post_id}' not found")
                if not is_admin and row["author_peer_id"] != peer_id:
                    raise PermissionError("Only the post author or an admin moderator can delete this post")
                topic_id = row["topic_id"]
                cursor.execute("DELETE FROM cyberspace_posts WHERE post_id = ?", (post_id,))
                cursor.execute("DELETE FROM cyberspace_votes WHERE target_type = 'post' AND target_id = ?", (post_id,))
                conn.commit()

            self._rebuild_indices()
            self._sync_to_s3_async()
            return {"status": "deleted", "post_id": post_id, "topic_id": topic_id}

    def vote_item(
        self,
        target_type: str,
        target_id: str,
        peer_id: str,
        direction: str = "up",
    ) -> Dict[str, Any]:
        """Upvote (+1), downvote (-1), or clear vote (0) on a topic or post."""
        target_type = (target_type or "topic").strip().lower()
        target_id = (target_id or "").strip()
        peer_id = (peer_id or "anonymous-peer").strip()
        if target_type not in ("topic", "post"):
            raise ValueError("target_type must be 'topic' or 'post'")
        if not target_id:
            raise ValueError("target_id is required")

        val_map = {"up": 1, "upvote": 1, "1": 1, "+1": 1, "down": -1, "downvote": -1, "-1": -1, "clear": 0, "0": 0}
        vote_val = val_map.get(str(direction).lower(), 1)
        now = time.time()

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if vote_val == 0:
                    cursor.execute(
                        "DELETE FROM cyberspace_votes WHERE target_type = ? AND target_id = ? AND peer_id = ?",
                        (target_type, target_id, peer_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO cyberspace_votes (target_type, target_id, peer_id, vote_val, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(target_type, target_id, peer_id) DO UPDATE SET
                            vote_val = excluded.vote_val,
                            updated_at = excluded.updated_at
                        """,
                        (target_type, target_id, peer_id, vote_val, now),
                    )

                cursor.execute(
                    "SELECT COALESCE(SUM(CASE WHEN vote_val > 0 THEN 1 ELSE 0 END), 0), COALESCE(SUM(CASE WHEN vote_val < 0 THEN 1 ELSE 0 END), 0), COALESCE(SUM(vote_val), 0) FROM cyberspace_votes WHERE target_type = ? AND target_id = ?",
                    (target_type, target_id),
                )
                upvotes, downvotes, total_score = cursor.fetchone()

                table = "cyberspace_topics" if target_type == "topic" else "cyberspace_posts"
                pk = "topic_id" if target_type == "topic" else "post_id"
                cursor.execute(
                    f"UPDATE {table} SET upvotes = ?, downvotes = ?, score = ? WHERE {pk} = ?",
                    (upvotes, downvotes, total_score, target_id),
                )
                conn.commit()

            self._rebuild_indices()
            self._sync_to_s3_async()
            return {
                "status": "voted",
                "target_type": target_type,
                "target_id": target_id,
                "peer_id": peer_id,
                "vote": vote_val,
                "upvotes": upvotes,
                "downvotes": downvotes,
                "score": total_score,
            }

    def accept_solution(self, topic_id: str, post_id: str, peer_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """Mark a specific reply as the Accepted Solution for a topic."""
        with self._lock:
            topic = self.get_topic(topic_id)
            if not topic:
                raise ValueError(f"Topic '{topic_id}' not found")
            if not is_admin and topic["author_peer_id"] != peer_id:
                raise PermissionError("Only the topic author or an admin moderator can accept a solution")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE cyberspace_posts SET is_accepted_solution = 0 WHERE topic_id = ?", (topic_id,))
                cursor.execute("UPDATE cyberspace_posts SET is_accepted_solution = 1 WHERE post_id = ? AND topic_id = ?", (post_id, topic_id))
                cursor.execute("UPDATE cyberspace_topics SET resolved = 1, accepted_post_id = ?, updated_at = ? WHERE topic_id = ?", (post_id, time.time(), topic_id))
                conn.commit()

            self._rebuild_indices()
            self._sync_to_s3_async()
            return self.get_topic(topic_id)

    def get_topic(self, topic_id: str, increment_views: bool = False) -> Optional[Dict[str, Any]]:
        """Retrieve a single topic with all posts and connected GraphRAG entities."""
        with self._lock:
            if increment_views:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("UPDATE cyberspace_topics SET view_count = view_count + 1 WHERE topic_id = ?", (topic_id,))
                    conn.commit()
            topics = self._load_all_topics_from_db()
            for t in topics:
                if t["topic_id"] == topic_id:
                    t_node = f"topic:{topic_id}"
                    neighbors = [
                        {
                            "node": nbr,
                            "label": self.graphrag.nodes.get(nbr, {}).get("label", nbr),
                            "type": self.graphrag.nodes.get(nbr, {}).get("type", "entity"),
                            "relation": rel,
                        }
                        for nbr, rel, _ in self.graphrag.adj.get(t_node, [])
                    ]
                    t["graph_connections"] = neighbors
                    return t
        return None

    def list_topics(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        mentioned_user: Optional[str] = None,
        mentioned_agent: Optional[str] = None,
        sort_by: str = "hot",
        verified_only: bool = False,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List discussion topics with filtering and sorting ('hot', 'new', 'top', 'discussed')."""
        with self._lock:
            topics = self._load_all_topics_from_db()

        if category and category.strip().lower() not in ("all", ""):
            cat_low = category.strip().lower()
            topics = [t for t in topics if t.get("category", "").lower() == cat_low]
        if tag:
            tag_low = tag.strip().lstrip("#").lower()
            topics = [t for t in topics if tag_low in [x.lower() for x in t.get("tags", [])]]
        if mentioned_user:
            u_low = mentioned_user.strip().lstrip("@").lower()
            topics = [
                t
                for t in topics
                if u_low == t.get("author_username", "").lower()
                or u_low in [x.lower() for x in t.get("user_mentions", [])]
                or any(p.get("author_username", "").lower() == u_low for p in t.get("posts", []))
            ]
        if mentioned_agent:
            a_low = mentioned_agent.strip().lstrip("@").lower()
            topics = [
                t
                for t in topics
                if a_low in [x.lower() for x in t.get("agent_mentions", [])]
                or any(p.get("author_username", "").lower() == a_low for p in t.get("posts", []))
            ]
        if verified_only:
            topics = [t for t in topics if t.get("author_verified")]

        sort_mode = (sort_by or "hot").strip().lower()
        if sort_mode == "new":
            topics.sort(key=lambda t: (t.get("pinned", False), t.get("created_at", 0.0)), reverse=True)
        elif sort_mode == "top":
            topics.sort(key=lambda t: (t.get("pinned", False), t.get("score", 0), t.get("reply_count", 0)), reverse=True)
        elif sort_mode == "discussed":
            topics.sort(key=lambda t: (t.get("pinned", False), t.get("reply_count", 0), t.get("updated_at", 0.0)), reverse=True)
        else:
            # 'hot' combines pinned status, score, reply count, and recency
            topics.sort(
                key=lambda t: (
                    t.get("pinned", False),
                    t.get("score", 0) * 2 + t.get("reply_count", 0) * 1.5,
                    t.get("updated_at", 0.0),
                ),
                reverse=True,
            )

        graph_snap = self.graphrag.get_full_graph_snapshot()
        roster = self.get_roster_and_profiles()
        return {
            "count": len(topics[:limit]),
            "total_topics": len(topics),
            "sort_by": sort_mode,
            "topics": topics[:limit],
            "categories": roster["categories"],
            "popular_tags": roster["popular_tags"],
            "available_agents": roster["agents"],
            "users_roster": roster["users"][:30],
            "graph_stats": graph_snap["stats"],
        }

    # =========================================================================
    # Hybrid Search: Okapi BM25 + Personalized PageRank GraphRAG + LLM Synthesis
    # =========================================================================

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        max_hops: int = 2,
        synthesize_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Search Cyberspace topics and posts using:
          - 'bm25': Okapi BM25 lexical information retrieval (with IDF/TF diagnostics)
          - 'graphrag': Personalized PageRank + Multi-hop Knowledge Graph activation spreading
          - 'hybrid' (default): Weighted fusion (0.55 BM25 + 0.45 GraphRAG) + Subgraph + Synthesis
        """
        query = (query or "").strip()
        mode = (mode or "hybrid").strip().lower()
        if not query:
            listed = self.list_topics(limit=top_k)
            return {
                "query": "",
                "mode": mode,
                "count": len(listed["topics"]),
                "results": listed["topics"],
                "bm25_diagnostics": self.bm25.get_diagnostics(""),
                "subgraph": self.graphrag.get_full_graph_snapshot(),
                "synthesis": "Showing active Cyberspace Knowledge Base discussions.",
            }

        with self._lock:
            bm25_raw = self.bm25.search(query, top_k=max(top_k * 2, 20))
            bm25_diag = self.bm25.get_diagnostics(query)
            bm25_map: Dict[str, Dict[str, Any]] = {r["topic_id"]: r for r in bm25_raw}
            graph_scores, topic_paths, subgraph = self.graphrag.retrieve_subgraph_and_scores(
                query=query,
                bm25_results=bm25_raw,
                max_hops=max_hops,
            )
            all_topics_map = {t["topic_id"]: t for t in self._load_all_topics_from_db()}

        candidate_ids = set(bm25_map.keys()) | set(graph_scores.keys())
        max_bm25 = max((r["bm25_score"] for r in bm25_raw), default=1.0) or 1.0
        max_graph = max(graph_scores.values(), default=1.0) or 1.0

        combined_results: List[Dict[str, Any]] = []
        for t_id in candidate_ids:
            topic = all_topics_map.get(t_id)
            if not topic:
                continue
            b_entry = bm25_map.get(t_id, {})
            raw_bm25 = float(b_entry.get("bm25_score", 0.0))
            raw_graph = float(graph_scores.get(t_id, 0.0))

            norm_bm25 = raw_bm25 / max_bm25 if max_bm25 > 0 else 0.0
            norm_graph = raw_graph / max_graph if max_graph > 0 else 0.0

            if mode == "bm25":
                if raw_bm25 <= 0:
                    continue
                final_score = raw_bm25
            elif mode == "graphrag":
                if raw_graph <= 0:
                    continue
                final_score = raw_graph
            else:
                final_score = round(0.55 * norm_bm25 + 0.45 * norm_graph, 4)

            combined_results.append(
                {
                    **topic,
                    "author_username": f"@{topic['author_username'].lstrip('@')}",
                    "user_mentions": [f"@{u.lstrip('@')}" for u in topic["user_mentions"]],
                    "agent_mentions": [f"@{a.lstrip('@')}" for a in topic["agent_mentions"]],
                    "score": round(final_score, 4),
                    "bm25_score": round(raw_bm25, 4),
                    "bm25_raw": round(raw_bm25, 4),
                    "graphrag_score": round(raw_graph, 4),
                    "matched_terms": b_entry.get("matched_terms", []),
                    "term_scores": b_entry.get("term_scores", {}),
                    "snippet": b_entry.get("snippet") or topic["body"][:200],
                    "highlighted_snippet": b_entry.get("snippet") or topic["body"][:200],
                    "graph_paths": topic_paths.get(t_id, []),
                }
            )

        combined_results.sort(key=lambda x: (x["score"], x["bm25_score"], x["graphrag_score"]), reverse=True)
        top_results = combined_results[:top_k]

        if top_results:
            top_titles = [f"\"{r['title']}\" (by {r['author_username']})" for r in top_results[:3]]
            involved_users = sorted(
                {u for r in top_results for u in ([r["author_username"]] + r["user_mentions"])}
            )
            involved_agents = sorted({a for r in top_results for a in r["agent_mentions"]})
            involved_tags = sorted({f"#{t.lstrip('#')}" for r in top_results for t in r["tags"][:5]})

            synthesis = (
                f"GraphRAG + BM25 Synthesis for '{query}' ({mode.upper()} mode): "
                f"Retrieved {len(top_results)} connected topic(s) led by {', '.join(top_titles)}. "
                f"Active Cyberspace Peers: {', '.join(involved_users[:6]) or 'none'}. "
                f"Tagged AI Agents: {', '.join(involved_agents[:5]) or 'none'}. "
                f"Knowledge Graph Concepts: {', '.join(involved_tags[:8])}."
            )

            if synthesize_llm and self.ai_router is not None and (self.ai_router.openrouter_key or os.environ.get("OPENROUTER_API_KEY")):
                try:
                    context_passages = "\n".join(
                        f"- [{r['topic_id']}] {r['title']} (by {r['author_username']}, BM25={r['bm25_score']}, GraphRAG={r['graphrag_score']}): {r['snippet']} | Paths: {'; '.join(r['graph_paths'][:2])}"
                        for r in top_results[:4]
                    )
                    resp = self.ai_router.dispatch_completion(
                        alias="gemini-brain",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are the TinCan Cyberspace GraphRAG + BM25 Synthesis Engine. "
                                    "Synthesize a concise 2-3 sentence answer to the user's query citing @usernames, @agents, and #tags from the retrieved context."
                                ),
                            },
                            {
                                "role": "user",
                                "content": f"Query: {query}\nMode: {mode.upper()}\nRetrieved GraphRAG + BM25 Context:\n{context_passages}",
                            },
                        ],
                        max_tokens=180,
                    )
                    llm_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if llm_text and not llm_text.startswith("[Simulated"):
                        synthesis = f"{synthesis}\n\n🤖 AI Knowledge Synthesis: {llm_text}"
                except Exception:
                    pass
        else:
            synthesis = f"No Cyberspace topics matched '{query}' in {mode.upper()} mode. Start a new topic and tag @gemini-brain!"

        return {
            "query": query,
            "mode": mode,
            "count": len(top_results),
            "results": top_results,
            "bm25_diagnostics": bm25_diag,
            "subgraph": subgraph,
            "synthesis": synthesis,
        }


__all__ = [
    "BM25Retriever",
    "BOARD_CATEGORIES",
    "CyberspaceBoardEngine",
    "CyberspaceGraphRAG",
    "KNOWN_AI_AGENTS",
    "parse_cyberspace_tags",
    "tokenize_for_bm25",
]
