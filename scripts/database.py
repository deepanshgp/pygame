import sqlite3
import os

class HighScoreDB:
    def __init__(self, db_path='data/high_scores.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database and create table if it doesn't exist"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS high_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    score INTEGER NOT NULL,
                    level_reached INTEGER NOT NULL,
                    date_achieved TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def save_high_score(self, score, level_reached):
        """Save a new high score with level reached"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO high_scores (score, level_reached) VALUES (?, ?)
            ''', (score, level_reached))
            
            conn.commit()
            conn.close()
            print(f"Saved high score: {score} at level {level_reached}")
        except Exception as e:
            print(f"Error saving high score: {e}")
    
    def get_high_score(self):
        """Get the highest score and level reached"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT score, level_reached FROM high_scores 
                ORDER BY score DESC, level_reached DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                print(f"Loaded high score from database: {result[0]} at level {result[1]}")
                return result[0], result[1]  # score, level_reached
            else:
                print("No high scores found in database, using defaults")
                return 0, 1  # default values
                
        except Exception as e:
            print(f"Error loading high score: {e}")
            return 0, 1  # default values on error
    
    def get_top_scores(self, limit=5):
        """Get top scores with level reached"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT score, level_reached, date_achieved 
                FROM high_scores 
                ORDER BY score DESC, level_reached DESC 
                LIMIT ?
            ''', (limit,))
            
            scores = cursor.fetchall()
            conn.close()
            return scores
        except Exception as e:
            print(f"Error getting top scores: {e}")
            return []