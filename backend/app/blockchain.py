import json
import time
import base64
import logging
from hashlib import sha256
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from .models import db, BlockModel, Voter, MempoolModel

logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        # Only hash the specific immutable data fields to ensure stability
        data = {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_string = json.dumps(data, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 4

    def __init__(self):
        self.unconfirmed_transactions = []
        # Chain is handled via DB, but we keep a local list for speed
        self.chain = []
        self.refresh_state()

    def refresh_state(self):
        """Always pull the LATEST chain and mempool from the Database to stay in sync"""
        # 1. Sync Chain
        blocks = BlockModel.query.order_by(BlockModel.index).all()
        self.chain = []
        if not blocks:
            self.create_genesis_block()
        else:
            for b_mod in blocks:
                block = Block(b_mod.index, json.loads(b_mod.transactions), b_mod.timestamp, b_mod.previous_hash, b_mod.nonce)
                block.hash = b_mod.hash
                self.chain.append(block)

        # 2. Sync Mempool
        pending = MempoolModel.query.order_by(MempoolModel.timestamp).all()
        self.unconfirmed_transactions = []
        for p in pending:
            self.unconfirmed_transactions.append({
                "voter_id": p.voter_id,
                "party": p.party,
                "timestamp": p.timestamp,
                "signature": p.signature,
                "public_key": p.public_key
            })

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.add_block_to_db(genesis_block)
        self.chain.append(genesis_block)

    def add_block_to_db(self, block):
        # Double-check for index collision (Race condition protection)
        existing = BlockModel.query.filter_by(index=block.index).first()
        if existing:
            return False
            
        b_mod = BlockModel(
            index=block.index,
            transactions=json.dumps(block.transactions),
            timestamp=block.timestamp,
            previous_hash=block.previous_hash,
            nonce=block.nonce,
            hash=block.hash # Must be set on block before calling this
        )
        db.session.add(b_mod)
        db.session.commit()
        return True

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        # 1. Verification
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            logger.error(f"[BLOCKCHAIN] Hash mismatch. Block prev: {block.previous_hash}, Chain last: {previous_hash}")
            return False
        if not self.is_valid_proof(block, proof):
            return False
        
        # 2. SEED THE HASH - Set it on the block BEFORE adding to DB
        block.hash = proof
        
        # 3. Persistence
        if self.add_block_to_db(block):
            self.chain.append(block)
            return True
        return False

    def is_valid_proof(self, block, block_hash):
        return (block_hash.startswith('0' * self.difficulty) and
                block_hash == block.compute_hash())

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_new_transaction(self, transaction):
        if self.verify_signature(transaction):
            # 1. Sync state to ensure we have the most recent pool
            self.refresh_state()
            
            # UNIQUE VOTER CHECK: Prevent same voter from appearing twice in pending pool
            voter_id = transaction['voter_id']
            if any(tx['voter_id'] == voter_id for tx in self.unconfirmed_transactions):
                logger.warning(f"[BLOCKCHAIN] Rejecting Tx: Voter {voter_id} already has a pending transaction.")
                return False

            # 2. Persist to DB Mempool immediately
            m_mod = MempoolModel(
                voter_id=voter_id,
                party=transaction['party'],
                timestamp=transaction['timestamp'],
                signature=transaction['signature'],
                public_key=transaction['public_key']
            )
            db.session.add(m_mod)
            db.session.commit()
            
            # 3. Re-Sync to confirm pool size after insertion
            self.refresh_state()
            pool_size = len(self.unconfirmed_transactions)
            logger.info(f"[BLOCKCHAIN] New Tx added. Global Pool Size: {pool_size}/3")
            
            # 4. Automatic Mining Trigger (Batch of 3)
            if pool_size >= 3:
                logger.info(f"[BLOCKCHAIN] Threshold reached ({pool_size}). Triggering auto-mine...")
                self.mine()
            return True
        return False

    def verify_signature(self, transaction):
        try:
            signature = base64.b64decode(transaction.get('signature'))
            public_key_bytes = base64.b64decode(transaction.get('public_key'))
            message = {
                "voter_id": transaction['voter_id'],
                "party": transaction['party'],
                "timestamp": transaction['timestamp']
            }
            message_bytes = json.dumps(message, sort_keys=True).encode()
            
            public_key = serialization.load_pem_public_key(public_key_bytes)
            public_key.verify(signature, message_bytes, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def mine(self, force=False):
        # 1. Sync state to ensure we have the most recent chain and transactions
        self.refresh_state()
        
        if not self.unconfirmed_transactions:
            return False
        
        # 2. STRICT BATCHING: Enforce 3 tx per block
        batch_size = 3
        if not force and len(self.unconfirmed_transactions) < batch_size:
            logger.info(f"[BLOCKCHAIN] Mining deferred. Global pool {len(self.unconfirmed_transactions)} < {batch_size}")
            return False

        # Take exactly 3 for auto-mining, or all for intentional forced mining
        mine_count = batch_size if not force else len(self.unconfirmed_transactions)
        tx_to_mine = self.unconfirmed_transactions[:mine_count]

        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                          transactions=tx_to_mine,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        if self.add_block(new_block, proof):
            # 3. Cleanup: Remove ONLY the mined transactions from DB Mempool
            try:
                # We identify transactions by voter_id and timestamp for precise deletion
                for tx in tx_to_mine:
                    MempoolModel.query.filter_by(
                        voter_id=tx['voter_id'], 
                        timestamp=tx['timestamp']
                    ).delete()
                db.session.commit()
            except Exception as e:
                logger.error(f"Mempool cleanup error: {e}")
                
            logger.info(f"[BLOCKCHAIN] Block #{new_block.index} SUCCESSFULLY SEALED with {len(tx_to_mine)} transactions.")
            self.refresh_state() # Final resync
            return True
        return False
