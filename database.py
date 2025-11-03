#!/usr/bin/env python3
"""
Database Manager for AI Insurance CRM
Handles SQLite database operations for persistent data storage
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        """Initialize database manager"""
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'insurance_crm.db')
        self.db_path = db_path
        
        # Ensure the directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Commission data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS commission_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        writing_agent TEXT,
                        writing_agent_npn TEXT,
                        npn TEXT,
                        insured_name TEXT,
                        account TEXT,
                        plan TEXT,
                        premium REAL,
                        commission_schedule TEXT,
                        split TEXT,
                        payment REAL,
                        payment_type TEXT,
                        effective_date TEXT,
                        coverage_month TEXT,
                        policy_state TEXT,
                        lives INTEGER,
                        year TEXT,
                        market TEXT,
                        memo TEXT,
                        associated_statement TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Document data table (from AI parsing)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT,
                        policy_number TEXT,
                        claim_number TEXT,
                        patient_name TEXT,
                        date_of_service TEXT,
                        provider_name TEXT,
                        total_amount REAL,
                        amount_paid REAL,
                        deductible REAL,
                        copay REAL,
                        coinsurance REAL,
                        service_description TEXT,
                        diagnosis_codes TEXT,
                        procedure_codes TEXT,
                        insurance_company TEXT,
                        claim_status TEXT,
                        notes TEXT,
                        parsed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Excel analysis cache table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS excel_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT UNIQUE,
                        analysis_data TEXT,
                        file_size_mb REAL,
                        total_rows INTEGER,
                        total_columns INTEGER,
                        analysis_date TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Upload history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS upload_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT,
                        file_type TEXT,
                        records_added INTEGER,
                        upload_status TEXT,
                        error_message TEXT,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Investors table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        lead_cost REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Leads table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        investor_id INTEGER NOT NULL,
                        insured_name TEXT,
                        lead_date TEXT,
                        cost REAL NOT NULL,
                        status TEXT DEFAULT 'active',
                        notes TEXT,
                        enrollment_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (investor_id) REFERENCES investors(id),
                        FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
                    )
                ''')
                
                # Enrollments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insured_name TEXT NOT NULL,
                        enrollment_date TEXT,
                        labor_cost REAL DEFAULT 15.00,
                        commission_data_id INTEGER,
                        lead_id INTEGER,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (commission_data_id) REFERENCES commission_data(id),
                        FOREIGN KEY (lead_id) REFERENCES leads(id)
                    )
                ''')
                
                # Users table for investor logins
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        investor_id INTEGER,
                        is_admin BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        FOREIGN KEY (investor_id) REFERENCES investors(id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def add_commission_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add commission records to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                added_count = 0
                for record in records:
                    cursor.execute('''
                        INSERT INTO commission_data (
                            writing_agent, writing_agent_npn, npn, insured_name, account,
                            plan, premium, commission_schedule, split, payment, payment_type,
                            effective_date, coverage_month, policy_state, lives, year,
                            market, memo, associated_statement
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.get('writing_agent', ''),
                        record.get('writing_agent_npn', ''),
                        record.get('npn', ''),
                        record.get('insured_name', ''),
                        record.get('account', ''),
                        record.get('plan', ''),
                        record.get('premium', 0.0),
                        record.get('commission_schedule', ''),
                        record.get('split', ''),
                        record.get('payment', 0.0),
                        record.get('payment_type', ''),
                        record.get('effective_date', ''),
                        record.get('coverage_month', ''),
                        record.get('policy_state', ''),
                        record.get('lives', 1),
                        record.get('year', ''),
                        record.get('market', ''),
                        record.get('memo', ''),
                        record.get('associated_statement', '')
                    ))
                    added_count += 1
                
                conn.commit()
                
                # Log upload history
                cursor.execute('''
                    INSERT INTO upload_history (file_name, file_type, records_added, upload_status)
                    VALUES (?, ?, ?, ?)
                ''', ('Commission CSV', 'CSV', added_count, 'Success'))
                
                return {
                    'success': True,
                    'records_added': added_count,
                    'message': f'Successfully added {added_count} commission records'
                }
                
        except Exception as e:
            logger.error(f"Error adding commission records: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to add commission records'
            }
    
    def add_document_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add document record to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO document_data (
                        file_name, policy_number, claim_number, patient_name, date_of_service,
                        provider_name, total_amount, amount_paid, deductible, copay, coinsurance,
                        service_description, diagnosis_codes, procedure_codes, insurance_company,
                        claim_status, notes, parsed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('file_name', ''),
                    record.get('policy_number', ''),
                    record.get('claim_number', ''),
                    record.get('patient_name', ''),
                    record.get('date_of_service', ''),
                    record.get('provider_name', ''),
                    record.get('total_amount', 0.0),
                    record.get('amount_paid', 0.0),
                    record.get('deductible', 0.0),
                    record.get('copay', 0.0),
                    record.get('coinsurance', 0.0),
                    record.get('service_description', ''),
                    ','.join(record.get('diagnosis_codes', [])),
                    ','.join(record.get('procedure_codes', [])),
                    record.get('insurance_company', ''),
                    record.get('claim_status', ''),
                    record.get('notes', ''),
                    record.get('parsed_at', '')
                ))
                
                conn.commit()
                
                # Log upload history
                cursor.execute('''
                    INSERT INTO upload_history (file_name, file_type, records_added, upload_status)
                    VALUES (?, ?, ?, ?)
                ''', (record.get('file_name', 'Document'), 'Document', 1, 'Success'))
                
                return {
                    'success': True,
                    'record_id': cursor.lastrowid,
                    'message': 'Document record added successfully'
                }
                
        except Exception as e:
            logger.error(f"Error adding document record: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to add document record'
            }
    
    def get_commission_data(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Get commission data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM commission_data 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting commission data: {str(e)}")
            return []
    
    def get_document_data(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Get document data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM document_data 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting document data: {str(e)}")
            return []
    
    def get_commission_summary(self) -> Dict[str, Any]:
        """Get commission data summary statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM commission_data')
                total_records = cursor.fetchone()[0]
                
                # Total payment
                cursor.execute('SELECT SUM(payment) FROM commission_data WHERE payment IS NOT NULL')
                total_payment = cursor.fetchone()[0] or 0
                
                # Total premium
                cursor.execute('SELECT SUM(premium) FROM commission_data WHERE premium IS NOT NULL')
                total_premium = cursor.fetchone()[0] or 0
                
                # Unique agents
                cursor.execute('SELECT COUNT(DISTINCT writing_agent) FROM commission_data WHERE writing_agent != ""')
                unique_agents = cursor.fetchone()[0]
                
                # Unique states
                cursor.execute('SELECT COUNT(DISTINCT policy_state) FROM commission_data WHERE policy_state != ""')
                unique_states = cursor.fetchone()[0]
                
                # Average payment
                cursor.execute('SELECT AVG(payment) FROM commission_data WHERE payment IS NOT NULL AND payment > 0')
                avg_payment = cursor.fetchone()[0] or 0
                
                return {
                    'total_records': total_records,
                    'total_payment': round(total_payment, 2),
                    'total_premium': round(total_premium, 2),
                    'unique_agents': unique_agents,
                    'unique_states': unique_states,
                    'average_payment': round(avg_payment, 2)
                }
                
        except Exception as e:
            logger.error(f"Error getting commission summary: {str(e)}")
            return {}
    
    def get_document_summary(self) -> Dict[str, Any]:
        """Get document data summary statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM document_data')
                total_records = cursor.fetchone()[0]
                
                # Total amount
                cursor.execute('SELECT SUM(total_amount) FROM document_data WHERE total_amount IS NOT NULL')
                total_amount = cursor.fetchone()[0] or 0
                
                # Total paid
                cursor.execute('SELECT SUM(amount_paid) FROM document_data WHERE amount_paid IS NOT NULL')
                total_paid = cursor.fetchone()[0] or 0
                
                # Unique patients
                cursor.execute('SELECT COUNT(DISTINCT patient_name) FROM document_data WHERE patient_name != ""')
                unique_patients = cursor.fetchone()[0]
                
                # Unique providers
                cursor.execute('SELECT COUNT(DISTINCT provider_name) FROM document_data WHERE provider_name != ""')
                unique_providers = cursor.fetchone()[0]
                
                return {
                    'total_records': total_records,
                    'total_amount': round(total_amount, 2),
                    'total_paid': round(total_paid, 2),
                    'unique_patients': unique_patients,
                    'unique_providers': unique_providers
                }
                
        except Exception as e:
            logger.error(f"Error getting document summary: {str(e)}")
            return {}
    
    def get_upload_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get upload history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM upload_history 
                    ORDER BY uploaded_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting upload history: {str(e)}")
            return []
    
    def search_data(self, table: str, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search data in specified table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if table == 'commission':
                    cursor.execute('''
                        SELECT * FROM commission_data 
                        WHERE writing_agent LIKE ? OR insured_name LIKE ? OR account LIKE ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit))
                elif table == 'document':
                    cursor.execute('''
                        SELECT * FROM document_data 
                        WHERE patient_name LIKE ? OR policy_number LIKE ? OR provider_name LIKE ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error searching data: {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table sizes
                cursor.execute('SELECT COUNT(*) FROM commission_data')
                commission_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM document_data')
                document_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM upload_history')
                upload_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM investors')
                investor_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM leads')
                leads_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM enrollments')
                enrollments_count = cursor.fetchone()[0]
                
                # Database file size
                db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
                
                return {
                    'commission_records': commission_count,
                    'document_records': document_count,
                    'total_uploads': upload_count,
                    'investor_count': investor_count,
                    'leads_count': leads_count,
                    'enrollments_count': enrollments_count,
                    'database_size_mb': round(db_size, 2),
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}
    
    # ============== INVESTOR MANAGEMENT ==============
    
    def add_investor(self, name: str, lead_cost: float) -> Dict[str, Any]:
        """Add a new investor"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO investors (name, lead_cost)
                    VALUES (?, ?)
                ''', (name, lead_cost))
                
                conn.commit()
                
                return {
                    'success': True,
                    'investor_id': cursor.lastrowid,
                    'message': f'Investor {name} added successfully'
                }
                
        except sqlite3.IntegrityError:
            return {
                'success': False,
                'error': f'Investor {name} already exists'
            }
        except Exception as e:
            logger.error(f"Error adding investor: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_investors(self) -> List[Dict[str, Any]]:
        """Get all investors"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM investors ORDER BY name')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting investors: {str(e)}")
            return []
    
    def update_investor(self, investor_id: int, name: str = None, lead_cost: float = None) -> Dict[str, Any]:
        """Update investor information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if name is not None:
                    cursor.execute('UPDATE investors SET name = ? WHERE id = ?', (name, investor_id))
                
                if lead_cost is not None:
                    cursor.execute('UPDATE investors SET lead_cost = ? WHERE id = ?', (lead_cost, investor_id))
                
                cursor.execute('UPDATE investors SET updated_at = ? WHERE id = ?', 
                             (datetime.now().isoformat(), investor_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': 'Investor updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating investor: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============== LEAD MANAGEMENT ==============
    
    def add_lead(self, investor_id: int, insured_name: str = None, lead_date: str = None, 
                 notes: str = None) -> Dict[str, Any]:
        """Add a new lead for an investor"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get investor's lead cost
                cursor.execute('SELECT lead_cost FROM investors WHERE id = ?', (investor_id,))
                result = cursor.fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'error': f'Investor ID {investor_id} not found'
                    }
                
                lead_cost = result[0]
                
                cursor.execute('''
                    INSERT INTO leads (investor_id, insured_name, lead_date, cost, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (investor_id, insured_name, lead_date or datetime.now().strftime('%Y-%m-%d'), 
                      lead_cost, notes))
                
                conn.commit()
                
                return {
                    'success': True,
                    'lead_id': cursor.lastrowid,
                    'cost': lead_cost,
                    'message': f'Lead added successfully with cost ${lead_cost}'
                }
                
        except Exception as e:
            logger.error(f"Error adding lead: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_leads(self, investor_id: int = None, status: str = None) -> List[Dict[str, Any]]:
        """Get leads, optionally filtered by investor or status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT l.*, i.name as investor_name, i.lead_cost as investor_lead_cost
                    FROM leads l
                    JOIN investors i ON l.investor_id = i.id
                    WHERE 1=1
                '''
                params = []
                
                if investor_id is not None:
                    query += ' AND l.investor_id = ?'
                    params.append(investor_id)
                
                if status is not None:
                    query += ' AND l.status = ?'
                    params.append(status)
                
                query += ' ORDER BY l.created_at DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting leads: {str(e)}")
            return []
    
    def link_lead_to_enrollment(self, lead_id: int, enrollment_id: int) -> Dict[str, Any]:
        """Link a lead to an enrollment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE leads 
                    SET enrollment_id = ?, status = 'converted', updated_at = ?
                    WHERE id = ?
                ''', (enrollment_id, datetime.now().isoformat(), lead_id))
                
                cursor.execute('''
                    UPDATE enrollments 
                    SET lead_id = ?, updated_at = ?
                    WHERE id = ?
                ''', (lead_id, datetime.now().isoformat(), enrollment_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': 'Lead linked to enrollment successfully'
                }
                
        except Exception as e:
            logger.error(f"Error linking lead to enrollment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============== ENROLLMENT MANAGEMENT ==============
    
    def add_enrollment(self, insured_name: str, enrollment_date: str = None, 
                      labor_cost: float = 15.00, commission_data_id: int = None,
                      lead_id: int = None, notes: str = None) -> Dict[str, Any]:
        """Add a new enrollment with labor cost"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure enrollment_date is properly formatted
                if not enrollment_date:
                    enrollment_date = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute('''
                    INSERT INTO enrollments (insured_name, enrollment_date, labor_cost, 
                                           commission_data_id, lead_id, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (insured_name, enrollment_date, labor_cost, commission_data_id, lead_id, notes))
                
                enrollment_id = cursor.lastrowid
                
                # If lead_id is provided, link them
                if lead_id:
                    cursor.execute('''
                        UPDATE leads 
                        SET enrollment_id = ?, status = 'converted', updated_at = ?
                        WHERE id = ?
                    ''', (enrollment_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), lead_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'enrollment_id': enrollment_id,
                    'labor_cost': labor_cost,
                    'message': f'Enrollment added with labor cost ${labor_cost}'
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error adding enrollment: {error_msg}")
            print(f"DEBUG: Database error: {error_msg}")  # Debug log
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_enrollments(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Get enrollments with related lead and investor info"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT e.*, 
                           l.id as lead_id, 
                           l.cost as lead_cost,
                           i.name as investor_name,
                           i.id as investor_id
                    FROM enrollments e
                    LEFT JOIN leads l ON e.lead_id = l.id
                    LEFT JOIN investors i ON l.investor_id = i.id
                    ORDER BY e.created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting enrollments: {str(e)}")
            return []
    
    # ============== REPORTING & ANALYTICS ==============
    
    def get_investor_contributions(self, investor_id: int = None) -> Dict[str, Any]:
        """Get total contributions (lead costs) by investor"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if investor_id:
                    # Single investor
                    cursor.execute('''
                        SELECT i.id, i.name, i.lead_cost,
                               COUNT(l.id) as total_leads,
                               SUM(l.cost) as total_contributed,
                               COUNT(CASE WHEN l.status = 'converted' THEN 1 END) as converted_leads,
                               COUNT(CASE WHEN l.status = 'active' THEN 1 END) as active_leads
                        FROM investors i
                        LEFT JOIN leads l ON i.id = l.investor_id
                        WHERE i.id = ?
                        GROUP BY i.id
                    ''', (investor_id,))
                else:
                    # All investors
                    cursor.execute('''
                        SELECT i.id, i.name, i.lead_cost,
                               COUNT(l.id) as total_leads,
                               SUM(l.cost) as total_contributed,
                               COUNT(CASE WHEN l.status = 'converted' THEN 1 END) as converted_leads,
                               COUNT(CASE WHEN l.status = 'active' THEN 1 END) as active_leads
                        FROM investors i
                        LEFT JOIN leads l ON i.id = l.investor_id
                        GROUP BY i.id
                        ORDER BY total_contributed DESC
                    ''')
                
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        'investor_id': row[0],
                        'investor_name': row[1],
                        'lead_cost': row[2],
                        'total_leads': row[3],
                        'total_contributed': round(row[4] or 0, 2),
                        'converted_leads': row[5],
                        'active_leads': row[6],
                        'conversion_rate': round((row[5] / row[3] * 100) if row[3] > 0 else 0, 2)
                    })
                
                return {
                    'success': True,
                    'investors': results
                }
                
        except Exception as e:
            logger.error(f"Error getting investor contributions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_labor_costs_summary(self) -> Dict[str, Any]:
        """Get total labor costs from enrollments"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_enrollments,
                        SUM(labor_cost) as total_labor_costs,
                        AVG(labor_cost) as avg_labor_cost,
                        MIN(labor_cost) as min_labor_cost,
                        MAX(labor_cost) as max_labor_cost
                    FROM enrollments
                ''')
                
                row = cursor.fetchone()
                
                return {
                    'success': True,
                    'total_enrollments': row[0],
                    'total_labor_costs': round(row[1] or 0, 2),
                    'avg_labor_cost': round(row[2] or 0, 2),
                    'min_labor_cost': round(row[3] or 0, 2),
                    'max_labor_cost': round(row[4] or 0, 2)
                }
                
        except Exception as e:
            logger.error(f"Error getting labor costs summary: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get comprehensive cost analysis including leads, labor, and commissions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total lead costs
                cursor.execute('SELECT SUM(cost) FROM leads')
                total_lead_costs = cursor.fetchone()[0] or 0
                
                # Total labor costs
                cursor.execute('SELECT SUM(labor_cost) FROM enrollments')
                total_labor_costs = cursor.fetchone()[0] or 0
                
                # Total commission payments
                cursor.execute('SELECT SUM(payment) FROM commission_data')
                total_commission = cursor.fetchone()[0] or 0
                
                # Total premium
                cursor.execute('SELECT SUM(premium) FROM commission_data')
                total_premium = cursor.fetchone()[0] or 0
                
                # Totals
                total_costs = total_lead_costs + total_labor_costs
                net_profit = total_commission - total_costs
                
                return {
                    'success': True,
                    'total_lead_costs': round(total_lead_costs, 2),
                    'total_labor_costs': round(total_labor_costs, 2),
                    'total_costs': round(total_costs, 2),
                    'total_commission': round(total_commission, 2),
                    'total_premium': round(total_premium, 2),
                    'net_profit': round(net_profit, 2),
                    'profit_margin': round((net_profit / total_commission * 100) if total_commission > 0 else 0, 2)
                }
                
        except Exception as e:
            logger.error(f"Error getting cost analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

if __name__ == "__main__":
    # Test the database manager
    db = DatabaseManager()
    
    print("🗄️  Testing Database Manager with Investor Tracking...")
    print()
    
    # Initialize investors
    print("💰 Adding investors...")
    eric_result = db.add_investor("Eric", 42.00)
    print(f"   Eric: {eric_result}")
    
    phillip_result = db.add_investor("Phillip", 40.00)
    print(f"   Phillip: {phillip_result}")
    print()
    
    # Get investors
    investors = db.get_investors()
    print(f"📋 Investors: {investors}")
    print()
    
    # Add sample leads
    if eric_result['success']:
        eric_id = eric_result['investor_id']
        lead1 = db.add_lead(eric_id, insured_name="John Doe", notes="Lead from referral")
        print(f"🎯 Added lead for Eric: {lead1}")
        
    if phillip_result['success']:
        phillip_id = phillip_result['investor_id']
        lead2 = db.add_lead(phillip_id, insured_name="Jane Smith", notes="Lead from online")
        print(f"🎯 Added lead for Phillip: {lead2}")
    print()
    
    # Add sample enrollment
    enrollment = db.add_enrollment(
        insured_name="John Doe",
        labor_cost=15.00,
        notes="Completed enrollment"
    )
    print(f"📝 Added enrollment: {enrollment}")
    print()
    
    # Get investor contributions
    contributions = db.get_investor_contributions()
    print(f"💵 Investor Contributions:")
    for investor in contributions.get('investors', []):
        print(f"   {investor['investor_name']}: ${investor['total_contributed']} ({investor['total_leads']} leads)")
    print()
    
    # Get labor costs summary
    labor_summary = db.get_labor_costs_summary()
    print(f"👷 Labor Costs Summary: {labor_summary}")
    print()
    
    # Get comprehensive cost analysis
    cost_analysis = db.get_cost_analysis()
    print(f"📊 Cost Analysis:")
    print(f"   Total Lead Costs: ${cost_analysis.get('total_lead_costs', 0)}")
    print(f"   Total Labor Costs: ${cost_analysis.get('total_labor_costs', 0)}")
    print(f"   Total Costs: ${cost_analysis.get('total_costs', 0)}")
    print(f"   Total Commission: ${cost_analysis.get('total_commission', 0)}")
    print(f"   Net Profit: ${cost_analysis.get('net_profit', 0)}")
    print()
    
    # Test database stats
    stats = db.get_database_stats()
    print(f"📈 Database Stats: {stats}")
    print()
    
    print("✅ Database Manager test complete!")

