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
        """Search through investor's CSV files using OpenAI."""
        try:
            if data_types is None:
                data_types = ['leads', 'enrollments']

            # Get investor name for file matching
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM investors WHERE id = ?', (investor_id,))
            investor_result = cursor.fetchone()
            conn.close()

            if not investor_result:
                return []

            investor_name = investor_result[0].lower()

            # Read data directly from CSV files
            all_data = []

            # Check for CSV files in uploads directory
            uploads_dir = '/data/uploads' if os.path.exists('/data') else 'uploads'
            print(f"DEBUG: Looking for CSV files in {uploads_dir}")

            if os.path.exists(uploads_dir):
                print(f"DEBUG: Uploads directory exists, contents: {os.listdir(uploads_dir)}")

                for filename in os.listdir(uploads_dir):
                    if not filename.lower().endswith('.csv'):
                        continue

                    print(f"DEBUG: Found CSV file: {filename}")

                    # Check if file belongs to this investor
                    if investor_name in filename.lower():
                        print(f"DEBUG: File {filename} belongs to investor {investor_name}")
                        file_path = os.path.join(uploads_dir, filename)

                        try:
                            import csv
                            with open(file_path, 'r', encoding='utf-8') as f:
                                reader = csv.DictReader(f)
                                rows = list(reader)
                                print(f"DEBUG: Read {len(rows)} rows from {filename}")

                            # Determine data type from filename
                            file_data_type = None
                            if 'lead' in filename.lower():
                                file_data_type = 'leads'
                            elif 'enrollment' in filename.lower():
                                file_data_type = 'enrollments'

                            print(f"DEBUG: Determined data type: {file_data_type}")

                            if file_data_type in data_types:
                                all_data.extend([{
                                    'type': file_data_type,
                                    'filename': filename,
                                    'data': rows
                                }])
                                print(f"DEBUG: Added {filename} to data sources")

                        except Exception as e:
                            print(f"Error reading {filename}: {e}")
                            continue
            else:
                print(f"DEBUG: Uploads directory does not exist: {uploads_dir}")

            if not all_data:
                return [{
                    'query': query,
                    'response': "I don't have any data files to search through yet. Please upload some CSV files first.",
                    'timestamp': datetime.now().isoformat()
                }]

            # Create a comprehensive data summary for the AI
            data_summary = []
            for data_item in all_data:
                data_type = data_item['type']
                filename = data_item['filename']
                rows = data_item['data']

                summary = f"\n{data_type.upper()} from {filename} ({len(rows)} records):\n"

                # Show sample records (first 10)
                for i, row in enumerate(rows[:10]):
                    first_name = row.get('First Name', '')
                    last_name = row.get('Last Name', '')
                    name = f"{first_name} {last_name}".strip()
                    created = row.get('Created', '')
                    tags = row.get('Tags', '')

                    summary += f"  {i+1}. {name} - {created}"
                    if tags:
                        summary += f" ({tags})"
                    summary += "\n"

                if len(rows) > 10:
                    summary += f"  ... and {len(rows) - 10} more records\n"

                data_summary.append(summary)

            # Create search prompt
            search_prompt = f"""
Based on the user query: "{query}"

Analyze the following CSV data and provide a helpful answer. The data includes leads and enrollments for {investor_name.title()}.

Data Summary:
{''.join(data_summary)}

Please provide a clear, accurate answer based on the data above. Include specific numbers and details when relevant.
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes CSV data to answer questions about leads and enrollments. Be specific and include numbers when possible."},
                    {"role": "user", "content": search_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            # Store chat history
            bot_response = response.choices[0].message.content

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (investor_id, user_message, bot_response)
                VALUES (?, ?, ?)
            ''', (investor_id, query, bot_response))
            conn.commit()
            conn.close()

            return [{
                'query': query,
                'response': bot_response,
                'timestamp': datetime.now().isoformat()
            }]

        except Exception as e:
            print(f"❌ Error searching CSV data: {e}")
            return []
    
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
