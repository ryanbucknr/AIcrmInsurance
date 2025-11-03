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
        """Process CSV data for a specific investor and create searchable chunks."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing chunks for this investor and data type
            cursor.execute('''
                DELETE FROM data_chunks 
                WHERE investor_id = ? AND data_type = ?
            ''', (investor_id, data_type))
            
            # Get data based on type
            if data_type == 'leads':
                query = '''
                    SELECT l.id, l.insured_name, l.lead_date, l.status, l.cost, l.notes,
                           i.name as investor_name, i.lead_cost as cost_per_lead
                    FROM leads l
                    JOIN investors i ON l.investor_id = i.id
                    WHERE l.investor_id = ?
                '''
            elif data_type == 'enrollments':
                query = '''
                    SELECT e.id, e.insured_name, e.enrollment_date, e.labor_cost, e.notes,
                           i.name as investor_name, i.lead_cost as cost_per_lead
                    FROM enrollments e
                    JOIN leads l ON e.lead_id = l.id
                    JOIN investors i ON l.investor_id = i.id
                    WHERE l.investor_id = ?
                '''
            else:
                return False
            
            cursor.execute(query, (investor_id,))
            rows = cursor.fetchall()
            
            if not rows:
                conn.close()
                return False
            
            # Get column names
            if data_type == 'leads':
                columns = ['id', 'insured_name', 'lead_date', 'status', 'cost', 'notes',
                          'investor_name', 'cost_per_lead']
            else:
                columns = ['id', 'insured_name', 'enrollment_date', 'labor_cost', 'notes',
                          'investor_name', 'cost_per_lead']
            
            # Create chunks of data (process in batches of 10 records)
            chunk_size = 10
            chunks = []
            
            for i in range(0, len(rows), chunk_size):
                chunk_rows = rows[i:i + chunk_size]
                chunk_text = f"Data for {data_type} (records {i+1}-{min(i+chunk_size, len(rows))}):\n\n"
                
                for row in chunk_rows:
                    record_text = ""
                    for j, value in enumerate(row):
                        if value is not None:
                            record_text += f"{columns[j]}: {value}\n"
                    chunk_text += record_text + "\n"
                
                # Create hash for uniqueness
                chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()
                
                # Store chunk
                cursor.execute('''
                    INSERT INTO data_chunks (investor_id, data_type, chunk_text, chunk_hash, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (investor_id, data_type, chunk_text, chunk_hash, 
                      json.dumps({'chunk_size': len(chunk_rows), 'start_index': i+1})))
                
                chunks.append(chunk_text)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Processed {len(rows)} {data_type} records into {len(chunks)} chunks for investor {investor_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing CSV data: {e}")
            return False
    
    def search_data(self, investor_id: int, query: str, data_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search through investor's data using OpenAI embeddings."""
        try:
            if data_types is None:
                data_types = ['leads', 'enrollments']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get relevant chunks
            chunks = []
            for data_type in data_types:
                cursor.execute('''
                    SELECT chunk_text, metadata FROM data_chunks
                    WHERE investor_id = ? AND data_type = ?
                ''', (investor_id, data_type))
                
                type_chunks = cursor.fetchall()
                chunks.extend([(chunk[0], chunk[1], data_type) for chunk in type_chunks])
            
            if not chunks:
                conn.close()
                return []
            
            # Use OpenAI to find most relevant chunks
            chunk_texts = [chunk[0] for chunk in chunks]
            
            # Create a prompt to find relevant data
            search_prompt = f"""
            Based on the user query: "{query}"
            
            Analyze the following data chunks and return the most relevant information.
            Focus on data that directly answers the user's question.
            
            Data chunks:
            {chr(10).join([f"Chunk {i+1}: {chunk[:500]}..." for i, chunk in enumerate(chunk_texts[:5])])}
            
            Return a JSON response with relevant data points that answer the query.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes data to answer user questions. Return relevant information in a clear, structured way."},
                    {"role": "user", "content": search_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Store chat history
            bot_response = response.choices[0].message.content
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
            print(f"❌ Error searching data: {e}")
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
