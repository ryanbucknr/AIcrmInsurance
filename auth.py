#!/usr/bin/env python3
"""
Authentication Manager for Investor Portal
Handles user authentication, password hashing, and session management
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'insurance_crm.db')
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
    
    def create_user(self, username, password, investor_id=None, is_admin=False):
        """Create a new user account"""
        try:
            password_hash = generate_password_hash(password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO users (username, password_hash, investor_id, is_admin)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, investor_id, is_admin))
                
                conn.commit()
                user_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'message': f'User {username} created successfully'
                }
                
        except sqlite3.IntegrityError:
            return {
                'success': False,
                'error': f'Username {username} already exists'
            }
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.*, i.name as investor_name
                    FROM users u
                    LEFT JOIN investors i ON u.investor_id = i.id
                    WHERE u.username = ?
                ''', (username,))
                
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    # Update last login
                    cursor.execute('''
                        UPDATE users SET last_login = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (user['id'],))
                    conn.commit()
                    
                    return {
                        'success': True,
                        'user': dict(user)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Invalid username or password'
                    }
                    
        except Exception as e:
            logger.error(f"Error verifying user: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.*, i.name as investor_name
                    FROM users u
                    LEFT JOIN investors i ON u.investor_id = i.id
                    WHERE u.id = ?
                ''', (user_id,))
                
                user = cursor.fetchone()
                
                if user:
                    return dict(user)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        try:
            password_hash = generate_password_hash(new_password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users SET password_hash = ?
                    WHERE id = ?
                ''', (password_hash, user_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': 'Password changed successfully'
                }
                
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def initialize_investor_accounts(self):
        """Initialize investor accounts for Eric and Phillip"""
        print("\n🔐 Initializing investor accounts...")
        
        # Get investors
        investors = self.db_manager.get_investors()
        eric = next((i for i in investors if i['name'] == 'Eric'), None)
        phillip = next((i for i in investors if i['name'] == 'Phillip'), None)
        
        if not eric or not phillip:
            print("❌ Eric and/or Phillip not found in investors table")
            print("   Please run initialize_investors.py first")
            return
        
        # Create Eric's account (username: eric, password: eric123)
        eric_result = self.create_user('eric', 'eric123', eric['id'], is_admin=False)
        if eric_result['success']:
            print(f"✅ Created login for Eric")
            print(f"   Username: eric")
            print(f"   Password: eric123")
        else:
            print(f"ℹ️  Eric account: {eric_result.get('error')}")
        
        # Create Phillip's account (username: phillip, password: phillip123)
        phillip_result = self.create_user('phillip', 'phillip123', phillip['id'], is_admin=False)
        if phillip_result['success']:
            print(f"✅ Created login for Phillip")
            print(f"   Username: phillip")
            print(f"   Password: phillip123")
        else:
            print(f"ℹ️  Phillip account: {phillip_result.get('error')}")
        
        # Create admin account (username: admin, password: admin123)
        admin_result = self.create_user('admin', 'admin123', None, is_admin=True)
        if admin_result['success']:
            print(f"✅ Created admin account")
            print(f"   Username: admin")
            print(f"   Password: admin123")
        else:
            print(f"ℹ️  Admin account: {admin_result.get('error')}")

if __name__ == "__main__":
    auth = AuthManager()
    auth.initialize_investor_accounts()
    
    print("\n" + "=" * 60)
    print("✅ Investor accounts initialized!")
    print("=" * 60)

