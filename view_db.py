import sqlite3

DATABASE = 'paper_generator.db'

def view_database():
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        
        print("\n" + "="*80)
        print("PAPER GENERATOR DATABASE - ALL TABLES")
        print("="*80)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database!")
            db.close()
            return
        
        # View each table
        for table in tables:
            table_name = table[0]
            print(f"\n\n{'='*80}")
            print(f"TABLE: {table_name.upper()}")
            print(f"{'='*80}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Print column headers
            col_names = [col[1] for col in columns]
            print(f"\nColumns: {', '.join(col_names)}\n")
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                print("(No data in this table)")
            else:
                # Print data in formatted table
                col_widths = [max(len(str(col[1])), max([len(str(row[i])) for row in rows] or [0])) for i, col in enumerate(columns)]
                
                # Print header
                header = " | ".join([col_names[i].ljust(col_widths[i]) for i in range(len(col_names))])
                print(header)
                print("-" * len(header))
                
                # Print rows
                for row in rows:
                    print(" | ".join([str(row[i]).ljust(col_widths[i]) for i in range(len(row))]))
                
                print(f"\nTotal rows: {len(rows)}")
        
        # Summary Statistics
        print(f"\n\n{'='*80}")
        print("SUMMARY STATISTICS")
        print(f"{'='*80}")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Total Users: {user_count}")
        
        # Count questions by type
        cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
        question_types = cursor.fetchall()
        print(f"\nQuestions by Type:")
        for qtype, count in question_types:
            print(f"  - {qtype}: {count}")
        
        # Count questions by subject
        cursor.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject")
        subjects = cursor.fetchall()
        print(f"\nQuestions by Subject:")
        for subject, count in subjects:
            print(f"  - {subject}: {count}")
        
        # Count papers
        cursor.execute("SELECT COUNT(*) FROM papers")
        paper_count = cursor.fetchone()[0]
        print(f"\nTotal Papers Generated: {paper_count}")
        
        print(f"\n{'='*80}\n")
        
        db.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    view_database()
