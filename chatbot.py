import os
import pandas as pd
import numpy as np
from openai import OpenAI
from typing import List, Dict, Any
import json
import sqlite3
from datetime import datetime
import hashlib

class ChatbotManager:
    def __init__(self, db_path: str = None):
        """Initialize the chatbot manager with OpenAI API and database connection."""
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'insurance_crm.db')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client with v1.x API
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize database tables for chatbot data
        self._init_chatbot_tables()
    
    def _init_chatbot_tables(self):
        """Initialize database tables for storing chatbot data and embeddings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table to store processed CSV data chunks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investor_id INTEGER NOT NULL,
                data_type TEXT NOT NULL,  -- 'leads' or 'enrollments'
                chunk_text TEXT NOT NULL,
                chunk_hash TEXT UNIQUE NOT NULL,
                metadata TEXT,  -- JSON string with additional info
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (investor_id) REFERENCES investors(id)
            )
        ''')
        
        # Table to store chat history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investor_id INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (investor_id) REFERENCES investors(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_csv_data(self, investor_id: int, data_type: str) -> bool:
        """Process CSV files for chatbot - now just verifies files exist and are readable."""
        try:
            # Get investor name
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM investors WHERE id = ?', (investor_id,))
            investor_result = cursor.fetchone()
            conn.close()

            if not investor_result:
                return False

            investor_name = investor_result[0].lower()

            # Check for CSV files in uploads directory
            uploads_dir = '/data/uploads' if os.path.exists('/data') else 'uploads'

            if not os.path.exists(uploads_dir):
                print(f"❌ Uploads directory not found: {uploads_dir}")
                return False

            csv_files_found = 0
            for filename in os.listdir(uploads_dir):
                if not filename.lower().endswith('.csv'):
                    continue

                # Check if file belongs to this investor and data type
                if (investor_name in filename.lower() and
                    ((data_type == 'leads' and 'lead' in filename.lower()) or
                     (data_type == 'enrollments' and 'enrollment' in filename.lower()))):

                    file_path = os.path.join(uploads_dir, filename)

                    try:
                        import csv
                        with open(file_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            rows = list(reader)

                        print(f"✅ Found {len(rows)} records in {filename}")
                        csv_files_found += 1

                    except Exception as e:
                        print(f"❌ Error reading {filename}: {e}")
                        continue

            if csv_files_found > 0:
                print(f"✅ Verified {csv_files_found} {data_type} CSV files for investor {investor_name}")
                return True
            else:
                print(f"❌ No {data_type} CSV files found for investor {investor_name}")
                return False

        except Exception as e:
            print(f"❌ Error processing CSV data: {e}")
            return False
    
    def search_data(self, investor_id: int, query: str, data_types: List[str] = None) -> List[Dict[str, Any]]:
        """Simple chatbot that reads from database, not CSV files"""
        try:
            if data_types is None:
                data_types = ['leads', 'enrollments']

            # Get data from database (simpler and more reliable)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get basic stats
            if 'leads' in data_types:
                cursor.execute('SELECT COUNT(*) as count FROM leads WHERE investor_id = ?', (investor_id,))
                leads_count = cursor.fetchone()[0]
            else:
                leads_count = 0

            if 'enrollments' in data_types:
                cursor.execute('''
                    SELECT COUNT(*) as count FROM enrollments e
                    JOIN leads l ON e.lead_id = l.id
                    WHERE l.investor_id = ?
                ''', (investor_id,))
                enrollments_count = cursor.fetchone()[0]
            else:
                enrollments_count = 0

            conn.close()

            # Calculate conversion rate
            conversion_rate = (enrollments_count / leads_count * 100) if leads_count > 0 else 0

            # Create simple response based on query
            query_lower = query.lower()

            if 'how many leads' in query_lower or 'lead count' in query_lower:
                response = f"You have {leads_count} leads in your portfolio."
            elif 'how many enrollment' in query_lower or 'enrollment count' in query_lower:
                response = f"You have {enrollments_count} enrollments."
            elif 'conversion rate' in query_lower or 'conversion' in query_lower:
                response = f"Your conversion rate is {conversion_rate:.1f}% ({enrollments_count} enrollments out of {leads_count} leads)."
            elif 'total' in query_lower or 'summary' in query_lower:
                response = f"Portfolio summary: {leads_count} leads, {enrollments_count} enrollments, {conversion_rate:.1f}% conversion rate."
            else:
                response = f"I can help you with information about your leads and enrollments. You currently have {leads_count} leads and {enrollments_count} enrollments, with a {conversion_rate:.1f}% conversion rate."

            # Store chat history
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (investor_id, user_message, bot_response)
                VALUES (?, ?, ?)
            ''', (investor_id, query, response))
            conn.commit()
            conn.close()

            return [{
                'query': query,
                'response': response,
                'timestamp': datetime.now().isoformat()
            }]

        except Exception as e:
            print(f"❌ Chatbot error: {e}")
            return [{
                'query': query,
                'response': "I'm having trouble accessing your data right now. Please try again later.",
                'timestamp': datetime.now().isoformat()
            }]
    
    def get_chat_history(self, investor_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat history for an investor."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_message, bot_response, timestamp
                FROM chat_history
                WHERE investor_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (investor_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'user_message': row[0],
                    'bot_response': row[1],
                    'timestamp': row[2]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            print(f"❌ Error getting chat history: {e}")
            return []
    
    def process_all_investor_data(self) -> bool:
        """Process data for all investors."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name FROM investors')
            investors = cursor.fetchall()
            conn.close()
            
            success_count = 0
            for investor_id, name in investors:
                print(f"Processing data for {name} (ID: {investor_id})...")
                
                leads_success = self.process_csv_data(investor_id, 'leads')
                enrollments_success = self.process_csv_data(investor_id, 'enrollments')
                
                if leads_success and enrollments_success:
                    success_count += 1
                    print(f"✅ Successfully processed data for {name}")
                else:
                    print(f"❌ Failed to process some data for {name}")
            
            print(f"✅ Processed data for {success_count}/{len(investors)} investors")
            return success_count == len(investors)
            
        except Exception as e:
            print(f"❌ Error processing all investor data: {e}")
            return False
