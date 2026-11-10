#!/usr/bin/env python3
"""
Peer Account Registration & Token Billing Service
Facilitates user onboarding for connected mesh peers and handles token billing,
credit balances, and usage ledger transactions.
"""

import os
import re
import sqlite3
import time
from typing import Dict, List, Optional


class PeerAccountRegistry:
    DEFAULT_INITIAL_TOKENS = 50_000
    DEFAULT_INITIAL_CREDIT_USD = 1.00

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = (
                os.environ.get("TINCAN_DATA_DIR")
                or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
                or os.path.dirname(os.path.abspath(__file__))
            )
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "peer_accounts.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    peer_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    created_at REAL NOT NULL,
                    status TEXT DEFAULT 'active',
                    token_balance INTEGER DEFAULT 50000,
                    credit_balance_usd REAL DEFAULT 1.00,
                    total_tokens_used INTEGER DEFAULT 0,
                    total_billed_usd REAL DEFAULT 0.0
                )
                """
            )
            # Ensure columns exist if schema previously existed
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [col[1] for col in cursor.fetchall()]
            if "token_balance" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN token_balance INTEGER DEFAULT 50000")
            if "credit_balance_usd" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN credit_balance_usd REAL DEFAULT 1.00")
            if "total_tokens_used" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN total_tokens_used INTEGER DEFAULT 0")
            if "total_billed_usd" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN total_billed_usd REAL DEFAULT 0.0")
            if "username" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN username TEXT DEFAULT ''")
            if "role" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN role TEXT DEFAULT 'Researcher / Student'")
            if "consent_pii" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN consent_pii INTEGER DEFAULT 1")
            if "consent_timestamp" not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN consent_timestamp REAL DEFAULT 0.0")

            # Ledger table for token audit transactions
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS token_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    peer_id TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    model TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    note TEXT DEFAULT '',
                    FOREIGN KEY(peer_id) REFERENCES accounts(peer_id)
                )
                """
            )
            conn.commit()

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return bool(re.match(pattern, email.strip()))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        cleaned = re.sub(r"[^\d+]", "", phone)
        return len(cleaned) >= 10

    def register_account(
        self,
        peer_id: str,
        full_name: str,
        phone_number: str,
        email: str,
        username: str = "",
        role: str = "Researcher / Student",
        consent_pii: bool = True,
        initial_tokens: int = DEFAULT_INITIAL_TOKENS,
        initial_credit_usd: float = DEFAULT_INITIAL_CREDIT_USD,
    ) -> Dict:
        """Register or update an account for a connected peer with mandatory identity & PII consent."""
        peer_id = (peer_id or "").strip()
        full_name = (full_name or "").strip()
        phone_number = (phone_number or "").strip()
        email = (email or "").strip().lower()
        username = (username or "").strip()
        if not username and full_name:
            username = full_name.split()[0].lower()

        if not peer_id:
            raise ValueError("peer_id is required")
        if not full_name or len(full_name) < 2:
            raise ValueError("Full Name is mandatory (minimum 2 characters)")
        if not username or len(username) < 2:
            raise ValueError("Username is mandatory (minimum 2 characters)")
        if not self.validate_email(email):
            raise ValueError(f"Invalid email address: {email}")
        if not self.validate_phone(phone_number):
            raise ValueError(f"Valid phone number is mandatory (minimum 10 digits): {phone_number}")
        if not consent_pii:
            raise ValueError("PII and operator telemetry consent is mandatory to access TinCan Mesh OS")

        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO accounts (
                    peer_id, full_name, phone_number, email, username, role,
                    consent_pii, consent_timestamp, created_at, status,
                    token_balance, credit_balance_usd, total_tokens_used, total_billed_usd
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, 0, 0.0)
                ON CONFLICT(peer_id) DO UPDATE SET
                    full_name=excluded.full_name,
                    phone_number=excluded.phone_number,
                    email=excluded.email,
                    username=excluded.username,
                    role=excluded.role,
                    consent_pii=excluded.consent_pii,
                    consent_timestamp=excluded.consent_timestamp,
                    created_at=excluded.created_at
                """,
                (
                    peer_id, full_name, phone_number, email, username, role,
                    1 if consent_pii else 0, now, now, initial_tokens, initial_credit_usd
                ),
            )
            conn.commit()

        return self.get_account_by_peer(peer_id)

    def get_account_by_peer(self, peer_id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE peer_id = ?", (peer_id.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_accounts(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def top_up_credits(self, peer_id: str, amount_usd: float = 0.0, tokens: int = 0) -> Dict:
        """Top up token balance and/or credit USD for an account."""
        peer_id = peer_id.strip()
        account = self.get_account_by_peer(peer_id)
        if not account:
            raise ValueError(f"Account for peer '{peer_id}' not found. Please register first.")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE accounts
                SET token_balance = token_balance + ?,
                    credit_balance_usd = credit_balance_usd + ?
                WHERE peer_id = ?
                """,
                (max(0, tokens), max(0.0, amount_usd), peer_id),
            )
            conn.commit()

        return self.get_account_by_peer(peer_id)

    def bill_tokens(
        self,
        peer_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost_usd: float,
        model: str,
        allow_overage: bool = True,
    ) -> Dict:
        """Bill a peer account for AI model token consumption."""
        peer_id = peer_id.strip()
        account = self.get_account_by_peer(peer_id)
        if not account:
            # Auto-provision temporary guest billing account if unregistered
            account = self.register_account(
                peer_id=peer_id,
                full_name=f"Peer ({peer_id[:8]})",
                phone_number="+10000000000",
                email=f"{peer_id[:12]}@mesh.local",
                initial_tokens=self.DEFAULT_INITIAL_TOKENS,
                initial_credit_usd=self.DEFAULT_INITIAL_CREDIT_USD,
            )

        current_balance = account["token_balance"]
        if not allow_overage and current_balance < total_tokens:
            raise ValueError(
                f"Insufficient tokens: requested {total_tokens} tokens, but balance is {current_balance}."
            )

        new_balance = max(0, current_balance - total_tokens)
        new_credit_usd = max(0.0, round(account["credit_balance_usd"] - cost_usd, 6))
        new_total_tokens = account["total_tokens_used"] + total_tokens
        new_total_billed = round(account["total_billed_usd"] + cost_usd, 6)
        now = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE accounts
                SET token_balance = ?,
                    credit_balance_usd = ?,
                    total_tokens_used = ?,
                    total_billed_usd = ?
                WHERE peer_id = ?
                """,
                (new_balance, new_credit_usd, new_total_tokens, new_total_billed, peer_id),
            )
            cursor.execute(
                """
                INSERT INTO token_ledger (
                    peer_id, prompt_tokens, completion_tokens, total_tokens,
                    cost_usd, model, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (peer_id, prompt_tokens, completion_tokens, total_tokens, cost_usd, model, now),
            )
            conn.commit()

        return {
            "peer_id": peer_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tokens_billed": total_tokens,
            "cost_usd": cost_usd,
            "model": model,
            "remaining_token_balance": new_balance,
            "remaining_credit_usd": new_credit_usd,
            "total_tokens_consumed": new_total_tokens,
            "total_billed_usd": new_total_billed,
        }

    def get_billing_summary(self, peer_id: str, limit: int = 10) -> Dict:
        """Retrieve token billing balance and recent ledger invoices for a peer."""
        account = self.get_account_by_peer(peer_id)
        if not account:
            return {"error": "Account not found", "peer_id": peer_id}

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT prompt_tokens, completion_tokens, total_tokens, cost_usd, model, timestamp
                FROM token_ledger
                WHERE peer_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (peer_id.strip(), limit),
            )
            ledger_entries = [dict(row) for row in cursor.fetchall()]

        return {
            "peer_id": peer_id,
            "full_name": account["full_name"],
            "email": account["email"],
            "token_balance": account["token_balance"],
            "credit_balance_usd": account["credit_balance_usd"],
            "total_tokens_used": account["total_tokens_used"],
            "total_billed_usd": account["total_billed_usd"],
            "recent_invoices": ledger_entries,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Peer Account & Token Billing Tool")
    subparsers = parser.add_subparsers(dest="command")

    reg_p = subparsers.add_parser("register", help="Register a connected peer account")
    reg_p.add_argument("--peer-id", required=True)
    reg_p.add_argument("--name", required=True)
    reg_p.add_argument("--phone", required=True)
    reg_p.add_argument("--email", required=True)

    bill_p = subparsers.add_parser("bill", help="Bill tokens for a peer")
    bill_p.add_argument("--peer-id", required=True)
    bill_p.add_argument("--tokens", type=int, default=1000)
    bill_p.add_argument("--cost", type=float, default=0.002)
    bill_p.add_argument("--model", default="gemini-brain")

    topup_p = subparsers.add_parser("topup", help="Top up account tokens/credits")
    topup_p.add_argument("--peer-id", required=True)
    topup_p.add_argument("--tokens", type=int, default=100000)
    topup_p.add_argument("--amount", type=float, default=5.00)

    summary_p = subparsers.add_parser("summary", help="Get billing summary for a peer")
    summary_p.add_argument("--peer-id", required=True)

    args = parser.parse_args()
    registry = PeerAccountRegistry()

    if args.command == "register":
        acc = registry.register_account(args.peer_id, args.name, args.phone, args.email)
        print(f"Registered {acc['peer_id']}: Balance = {acc['token_balance']} tokens (${acc['credit_balance_usd']})")
    elif args.command == "bill":
        rec = registry.bill_tokens(
            peer_id=args.peer_id,
            prompt_tokens=args.tokens // 2,
            completion_tokens=args.tokens // 2,
            total_tokens=args.tokens,
            cost_usd=args.cost,
            model=args.model,
        )
        print(f"Billed {args.tokens} tokens to {args.peer_id}. Remaining balance: {rec['remaining_token_balance']}")
    elif args.command == "topup":
        acc = registry.top_up_credits(args.peer_id, amount_usd=args.amount, tokens=args.tokens)
        print(f"Top-up successful! New balance: {acc['token_balance']} tokens (${acc['credit_balance_usd']})")
    elif args.command == "summary":
        summary = registry.get_billing_summary(args.peer_id)
        print(f"Billing Summary: {summary}")
    else:
        parser.print_help()
