from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb
import MySQLdb.cursors
import re
from functools import wraps
import random
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL Configuration
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'Avinash@2006'
MYSQL_DB = 'paper_generator'
MYSQL_PORT = 3306

app.config['MYSQL_HOST'] = MYSQL_HOST
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
app.config['MYSQL_PORT'] = MYSQL_PORT

mysql = MySQL(app)

# Utility helper functions
def normalize_text(s):
    if s is None:
        return ''
    return str(s).strip()

def normalize_key(s):
    return normalize_text(s).lower()

def normalize_qtype(q):
    """Normalize question type to a canonical value used in DB."""
    if not q:
        return ''
    s = normalize_key(q)
    if s in ('mcq', 'multiple choice', 'multiplechoice'):
        return 'MCQ'
    if s in ('one sentence', 'onesentence', 'one-sentence'):
        return 'One Sentence'
    if s in ('short answer', 'shortanswer', 'short-answer'):
        return 'Short Answer'
    if s in ('long answer', 'longanswer', 'long-answer'):
        return 'Long Answer'
    if s in ('descriptive', 'desc'):
        return 'Descriptive'
    return q.strip()

def is_valid_question_type(qtype):
    return normalize_qtype(qtype) in {'MCQ', 'One Sentence', 'Short Answer', 'Long Answer', 'Descriptive'}

# Create database and tables using direct MySQLdb connection
def init_db():
    try:
        # Connect to MySQL without specifying database
        conn = MySQLdb.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
            charset='utf8mb4',
            cursorclass=MySQLdb.cursors.DictCursor
        )

        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS paper_generator")
        print("✓ Database created/verified")
        
        # Use the database
        cursor.execute("USE paper_generator")
        
        # Create users table (single creation) and ensure constraints
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('teacher', 'admin') DEFAULT 'teacher',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_username_email (username, email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ Users table created/verified")

        # Create questions table (normalized)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                teacher_id INT NOT NULL,
                subject VARCHAR(100) NOT NULL,
                chapter VARCHAR(100) NOT NULL,
                question_text LONGTEXT NOT NULL,
                marks INT NOT NULL,
                difficulty VARCHAR(20) DEFAULT 'medium',
                year VARCHAR(10),
                semester VARCHAR(10),
                question_type ENUM('MCQ', 'One Sentence', 'Short Answer', 'Long Answer', 'Descriptive') NOT NULL DEFAULT 'Descriptive',
                mcq_options JSON NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_subject (subject),
                INDEX idx_chapter (chapter),
                INDEX idx_teacher_id (teacher_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ Questions table created/verified")

        # Create papers table (normalized)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                subject VARCHAR(100) NOT NULL,
                total_marks INT,
                questions_json LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_subject (subject)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✓ Papers table created/verified")
        
        # After creating tables, ensure compatibility / migrations
        try:
            admin_id = ensure_default_admin(cursor, conn)
            ensure_questions_teacher_id(cursor, conn, admin_id)
        except Exception as migrate_err:
            print(f"✗ Schema migration error: {migrate_err}")
            # continue; init proceeds

        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Database initialization successful")
        return True
    
    except MySQLdb.Error as e:
        print(f"✗ MySQL Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL service is running: net start MySQL80")
        print("2. Check your password is correct in app.py")
        print("3. If you don't have a password, leave it blank")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_db_connection():
    try:
        with app.app_context():
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        print("✓ Flask-MySQLdb connection successful")
        return True
    except Exception as e:
        print(f"✗ Connection test failed: {str(e)}")
        return False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = normalize_text(data.get('username', ''))
            email = normalize_text(data.get('email', '')).lower()
            password = data.get('password', '').strip()
            role = data.get('role', 'teacher')
            
            print(f"Registration attempt: {username} ({email})")
            
            if not username or not email or not password:
                return jsonify({'success': False, 'message': 'Please fill all fields'}), 400
            
            if len(username) < 3:
                return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
            
            if len(password) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({'success': False, 'message': 'Invalid email format'}), 400
            
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
                account = cursor.fetchone()
                
                if account:
                    cursor.close()
                    return jsonify({'success': False, 'message': 'Email already exists'}), 400
                
                hashed = generate_password_hash(password)
                cursor.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)',
                              (username, email, hashed, role))
                mysql.connection.commit()
                cursor.close()
                
                print(f"✓ User registered: {email}")
                return jsonify({'success': True, 'message': 'Registration successful!'}), 201
            
            except MySQLdb.Error as db_error:
                print(f"Database error: {str(db_error)}")
                return jsonify({'success': False, 'message': 'Database error'}), 500
        
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({'success': False, 'message': 'Registration failed'}), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = normalize_text(data.get('email', '')).lower()
            password = data.get('password', '').strip()
            
            print(f"Login attempt: {email}")
            
            if not email or not password:
                return jsonify({'success': False, 'message': 'Please fill all fields'}), 400
            
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
                account = cursor.fetchone()
                cursor.close()
                
                if account and check_password_hash(account['password'], password):
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    session['role'] = account['role']
                    print(f"✓ Login successful: {email}")
                    return jsonify({'success': True, 'message': 'Login successful'}), 200
                else:
                    print(f"✗ Login failed: {email}")
                    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
            except MySQLdb.Error as db_error:
                print(f"Database error: {str(db_error)}")
                return jsonify({'success': False, 'message': 'Database error'}), 500
        
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({'success': False, 'message': 'Login failed'}), 500
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/view-questions')
@login_required
def view_questions():
    return render_template('view_questions.html')

@app.route('/add-question', methods=['GET', 'POST'])
@login_required
def add_question():
	if request.method == 'GET':
		return render_template('add_question.html')

	try:
		if request.is_json:
			data = request.get_json()
		else:
			form = request.form
			data = {
				'subject': form.get('subject', ''),
				'chapter': form.get('chapter', ''),
				'question': form.get('question', ''),
				'marks': form.get('marks', ''),
				'difficulty': form.get('difficulty', 'medium'),
				'year': form.get('year', ''),
				'semester': form.get('semester', ''),
				'questionType': form.get('questionType', ''),
				'mcqOptions': form.getlist('mcqOptions') if 'mcqOptions' in form else None
			}
		
		if session.get('role') != 'teacher':
			if request.is_json:
				return jsonify({'success': False, 'message': 'Only teachers can add questions'}), 403
			flash('Only teachers can add questions', 'error')
			return redirect(url_for('add_question'))

		print(f"\n📝 Received data: {data}")

		subject_raw = data.get('subject', '')
		subject_display = normalize_text(subject_raw)
		chapter = normalize_text(data.get('chapter', ''))
		question_text = normalize_text(data.get('question', ''))
		marks_raw = data.get('marks')
		try:
			marks = int(marks_raw)
		except Exception:
			marks = None
		difficulty = normalize_text(data.get('difficulty', 'medium')) or 'medium'
		year = normalize_text(data.get('year'))
		semester = normalize_text(data.get('semester'))
		question_type = normalize_qtype(data.get('questionType'))
		mcq_options = data.get('mcqOptions')

		print(f"Validation Check: Subject: {subject_display}, Chapter: {chapter}, Question: {question_text[:50] if question_text else 'EMPTY'}, Marks: {marks}, Type: {question_type}, Teacher ID: {session.get('id')}")

		if not subject_display or not chapter or not question_text or marks is None or not question_type:
			missing = []
			if not subject_display: missing.append('Subject')
			if not chapter: missing.append('Chapter')
			if not question_text: missing.append('Question Text')
			if marks is None: missing.append('Marks')
			if not question_type: missing.append('Question Type')
			error_msg = f'Missing fields: {", ".join(missing)}'
			print(f"❌ {error_msg}")
			if request.is_json:
				return jsonify({'success': False, 'message': error_msg}), 400
			flash(error_msg, 'error')
			return render_template('add_question.html', error=error_msg, form=data)

		if marks <= 0:
			if request.is_json:
				return jsonify({'success': False, 'message': 'Marks must be greater than 0'}), 400
			flash('Marks must be greater than 0', 'error')
			return render_template('add_question.html', error='Marks must be greater than 0', form=data)

		if not is_valid_question_type(question_type):
			if request.is_json:
				return jsonify({'success': False, 'message': 'Invalid question type'}), 400
			flash('Invalid question type', 'error')
			return render_template('add_question.html', error='Invalid question type', form=data)

		mcq_json = None
		if question_type == 'MCQ' and mcq_options:
			try:
				mcq_json = json.dumps(mcq_options)
			except Exception:
				mcq_json = json.dumps(list(mcq_options) if mcq_options else [])
			print(f"  MCQ Options: {mcq_options}")

		try:
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute('SELECT id FROM users WHERE id = %s', (session.get('id'),))
			teacher = cursor.fetchone()
			
			if not teacher:
				cursor.close()
				print(f"❌ Teacher ID {session.get('id')} not found in database")
				if request.is_json:
					return jsonify({'success': False, 'message': 'Invalid teacher session. Please login again.'}), 401
				flash('Invalid teacher session. Please login again.', 'error')
				return redirect(url_for('login'))

			print(f"\n📤 Inserting question: Teacher ID: {session.get('id')}, Subject: {subject_display}, Chapter: {chapter}, Type: {question_type}, Marks: {marks}")

			cursor.execute('''
				INSERT INTO questions 
				(teacher_id, subject, chapter, question_text, marks, difficulty, year, semester, question_type, mcq_options) 
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			''', (session.get('id'), subject_display, chapter, question_text, marks, difficulty, year, semester, question_type, mcq_json))
			
			mysql.connection.commit()
			cursor.close()

			print(f"✅ Question added successfully!")
			if request.is_json:
				return jsonify({'success': True, 'message': 'Question added successfully!'}), 201

			flash('Question added successfully!', 'success')
			return redirect(url_for('add_question'))

		except MySQLdb.Error as db_error:
			print(f"❌ Database error: {str(db_error)}")
			if request.is_json:
				return jsonify({'success': False, 'message': f'Database error: {str(db_error)}'}), 500
			flash('Database error while saving question', 'error')
			return render_template('add_question.html', error=f'Database error: {str(db_error)}', form=data)

	except Exception as e:
		print(f"❌ Error: {str(e)}")
		if request.is_json:
			return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
		flash(f'Error: {str(e)}', 'error')
		return render_template('add_question.html', error=f'Error: {str(e)}', form={})

@app.route('/get-questions')
@login_required
def get_questions():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if session['role'] == 'teacher':
            cursor.execute('SELECT * FROM questions WHERE teacher_id = %s', (session['id'],))
        else:
            cursor.execute('SELECT * FROM questions')
        
        questions = cursor.fetchall()
        cursor.close()
        return jsonify({'questions': questions}), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'questions': []}), 200

@app.route('/get-all-questions')
@login_required
def get_all_questions():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM questions ORDER BY subject, chapter, created_at DESC')
        questions = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'questions': questions}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-papers')
@login_required
def get_papers():
    """Retrieve all papers generated by the logged-in user."""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM papers WHERE user_id = %s ORDER BY created_at DESC', (session.get('id'),))
        papers = cursor.fetchall()
        
        # Parse questions_json for each paper
        for paper in papers:
            try:
                paper['questions'] = json.loads(paper.get('questions_json', '[]'))
            except Exception as e:
                print(f"Error parsing questions_json for paper {paper['id']}: {e}")
                paper['questions'] = []
        
        cursor.close()
        return jsonify({'success': True, 'papers': papers}), 200
    except Exception as e:
        print(f"Error fetching papers: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-paper/<int:paper_id>')
@login_required
def get_paper(paper_id):
    """Retrieve a specific paper with its questions."""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM papers WHERE id = %s AND user_id = %s', (paper_id, session.get('id')))
        paper = cursor.fetchone()
        cursor.close()
        
        if not paper:
            return jsonify({'success': False, 'message': 'Paper not found'}), 404
        
        try:
            paper['questions'] = json.loads(paper.get('questions_json', '[]'))
        except Exception as e:
            print(f"Error parsing questions_json: {e}")
            paper['questions'] = []
        
        print(f"✓ Retrieved paper #{paper_id} with {len(paper['questions'])} questions")
        return jsonify({'success': True, 'paper': paper}), 200
    except Exception as e:
        print(f"Error fetching paper: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Update generate_paper to use the serializer
@app.route('/generate-paper', methods=['POST'])
@login_required
def generate_paper():
    try:
        data = request.get_json()
        subject = normalize_text(data.get('subject', ''))
        subject_display = subject
        subject_norm = normalize_key(subject)
        selected_chapters_raw = data.get('selectedChapters', [])
        exam_type = normalize_text(data.get('examType', ''))
        course_code = normalize_text(data.get('courseCode', ''))
        exam_time = int(data.get('examTime', 60) or 60)
        question_structure = data.get('questionStructure', [])
        total_marks_requested = data.get('totalMarks', 0)
        
        print(f"\n🔍 GENERATE PAPER DEBUG START")
        print(f"Subject: '{subject_display}' (norm: '{subject_norm}')")
        print(f"Chapters: {selected_chapters_raw}")
        print(f"Exam Type: {exam_type}")
        print(f"Question Structure: {question_structure}")
        
        if not subject_display:
            return jsonify({'success': False, 'message': 'Please select subject'}), 400
        
        # If we have question structure, fetch questions accordingly
        if question_structure and len(question_structure) > 0:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Fetch questions for each part of the structure
                for q_struct in question_structure:
                    chapter = q_struct.get('chapter', '')
                    chapter_norm = normalize_key(chapter)
                    
                    # Fetch questions for Part A
                    if q_struct.get('partA') and q_struct['partA'].get('count', 0) > 0:
                        part_a = q_struct['partA']
                        qtype = normalize_qtype(part_a.get('type', ''))
                        count = part_a.get('count', 0)
                        marks_each = part_a.get('marksEach', 0)
                        
                        print(f"Part A Query - Subject: '{subject_norm}', Chapter: '{chapter_norm}', Type: '{qtype}', Marks: {marks_each}, Count: {count}")
                        
                        query = '''
                            SELECT * FROM questions 
                            WHERE LOWER(TRIM(subject)) = %s 
                            AND LOWER(TRIM(chapter)) = %s 
                            AND question_type = %s
                            AND marks = %s
                            ORDER BY RAND()
                            LIMIT %s
                        '''
                        cursor.execute(query, (subject_norm, chapter_norm, qtype, marks_each, count))
                        part_a['questions'] = cursor.fetchall()
                        print(f"Fetched {len(part_a['questions'])} questions for Part A ({qtype}, {marks_each} marks)")
                        
                        # Debug: If no questions found with exact marks, show what's available
                        if len(part_a['questions']) == 0:
                            cursor.execute('''
                                SELECT DISTINCT marks FROM questions 
                                WHERE LOWER(TRIM(subject)) = %s 
                                AND LOWER(TRIM(chapter)) = %s 
                                AND question_type = %s
                            ''', (subject_norm, chapter_norm, qtype))
                            available_marks = cursor.fetchall()
                            print(f"  No {marks_each}-mark questions found. Available marks: {[m['marks'] for m in available_marks]}")
                    
                    # Fetch questions for Part B
                    if q_struct.get('partB') and q_struct['partB'].get('count', 0) > 0:
                        part_b = q_struct['partB']
                        qtype = normalize_qtype(part_b.get('type', ''))
                        count = part_b.get('count', 0)
                        marks_each = part_b.get('marksEach', 0)
                        
                        print(f"Part B Query - Subject: '{subject_norm}', Chapter: '{chapter_norm}', Type: '{qtype}', Marks: {marks_each}, Count: {count}")
                        
                        query = '''
                            SELECT * FROM questions 
                            WHERE LOWER(TRIM(subject)) = %s 
                            AND LOWER(TRIM(chapter)) = %s 
                            AND question_type = %s
                            AND marks = %s
                            ORDER BY RAND()
                            LIMIT %s
                        '''
                        cursor.execute(query, (subject_norm, chapter_norm, qtype, marks_each, count))
                        part_b['questions'] = cursor.fetchall()
                        print(f"Fetched {len(part_b['questions'])} questions for Part B ({qtype}, {marks_each} marks)")
                        
                        # Debug: If no questions found with exact marks, show what's available
                        if len(part_b['questions']) == 0:
                            cursor.execute('''
                                SELECT DISTINCT marks FROM questions 
                                WHERE LOWER(TRIM(subject)) = %s 
                                AND LOWER(TRIM(chapter)) = %s 
                                AND question_type = %s
                            ''', (subject_norm, chapter_norm, qtype))
                            available_marks = cursor.fetchall()
                            print(f"  No {marks_each}-mark questions found. Available marks: {[m['marks'] for m in available_marks]}")
                
                # Create paper with structured questions
                paper = {
                    'title': f'{subject_display} Question Paper',
                    'subject': subject_display,
                    'courseCode': course_code,
                    'examType': exam_type,
                    'examTime': exam_time,
                    'total_marks': total_marks_requested,
                    'questionStructure': question_structure,
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Save to database
                questions_json = json.dumps(question_structure, default=json_serializer)
                cursor.execute('INSERT INTO papers (user_id, subject, total_marks, questions_json) VALUES (%s, %s, %s, %s)',
                              (session.get('id'), subject_display, total_marks_requested, questions_json))
                mysql.connection.commit()
                cursor.close()
                
                print(f"✓ Paper generated with structured questions")
                print(f"🔍 GENERATE PAPER DEBUG END - SUCCESS\n")
                return jsonify({'success': True, 'paper': paper}), 200
                
            except MySQLdb.Error as db_error:
                print(f"Database error: {str(db_error)}")
                return jsonify({'success': False, 'message': f'Database error: {str(db_error)}'}), 500
        
        # Fallback to old method if no structure
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            chapter_names = []
            chapter_questions_dist = {}
            warnings = []
            
            for chapter_data in selected_chapters_raw or []:
                try:
                    if isinstance(chapter_data, dict):
                        chapter_name = normalize_text(chapter_data.get('name', ''))
                        distribution = chapter_data.get('distribution', {}) or {}
                    else:
                        chapter_name = normalize_text(chapter_data)
                        distribution = {}
                    
                    if not chapter_name:
                        continue
                    
                    chapter_names.append(chapter_name)
                    
                    if distribution and isinstance(distribution, dict):
                        def safe_int(x, default=0):
                            try:
                                return int(x or default)
                            except Exception:
                                return default
                        
                        chapter_questions_dist[chapter_name] = {
                            'mcq': {'count': safe_int(distribution.get('mcq', {}).get('count', 0)), 'marks': safe_int(distribution.get('mcq', {}).get('marks', 1))},
                            'oneSentence': {'count': safe_int(distribution.get('oneSentence', {}).get('count', 0)), 'marks': safe_int(distribution.get('oneSentence', {}).get('marks', 2))},
                            'longAnswer': {'count': safe_int(distribution.get('longAnswer', {}).get('count', 0)), 'marks': safe_int(distribution.get('longAnswer', {}).get('marks', 5))}
                        }
                except Exception as e:
                    print(f"Error processing chapter: {str(e)}")
                    continue
            
            print(f"Extracted chapter_names: {chapter_names}")
            print(f"Chapter distributions: {chapter_questions_dist}")
            
            # If no chapters specified, use all questions from subject
            if not chapter_names:
                print(f"ℹ️ No chapters specified; fetching all questions for subject '{subject_norm}'")
                cursor.execute('SELECT * FROM questions WHERE LOWER(TRIM(subject)) = %s', (subject_norm,))
                all_questions = cursor.fetchall()
                print(f"📊 Exact match found: {len(all_questions)} questions")
                
                if not all_questions:
                    like_pattern = f"%{subject_norm}%"
                    cursor.execute('SELECT * FROM questions WHERE LOWER(subject) LIKE %s', (like_pattern,))
                    all_questions = cursor.fetchall()
                    print(f"📊 LIKE fallback found: {len(all_questions)} questions")
                
                if all_questions:
                    # Log what we found
                    for q in all_questions:
                        print(f"  Q#{q['id']}: '{q['subject']}' / '{q['chapter']}' / Type: {q['question_type']} / Marks: {q['marks']}")
                
                if not all_questions:
                    if exam_type == 'Class Test':
                        paper = {
                            'title': f'{subject_display} Question Paper',
                            'subject': subject_display,
                            'courseCode': course_code,
                            'examType': exam_type,
                            'examTime': exam_time,
                            'total_marks': 0,
                            'questions': [],
                            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        cursor.close()
                        return jsonify({'success': True, 'paper': paper, 'warnings': ['No questions found; generated empty paper']}), 200
                    cursor.close()
                    return jsonify({'success': False, 'message': 'No questions found for selected subject'}), 400
                
                # Use all questions (no filtering by type/distribution if not specified)
                selected_questions = list(all_questions)
                print(f"✓ Selected {len(selected_questions)} questions (no filtering applied)")
                
                actual_total_marks = sum(int(q.get('marks', 0) or 0) for q in selected_questions)
                print(f"✓ Total marks: {actual_total_marks}")
                
                paper = {
                    'title': f'{subject_display} Question Paper',
                    'subject': subject_display,
                    'courseCode': course_code,
                    'examType': exam_type,
                    'examTime': exam_time,
                    'total_marks': actual_total_marks,
                    'questions': selected_questions,
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                questions_json = json.dumps(selected_questions, default=json_serializer)
                cursor.execute('INSERT INTO papers (user_id, subject, total_marks, questions_json) VALUES (%s, %s, %s, %s)',
                              (session.get('id'), subject_display, actual_total_marks, questions_json))
                mysql.connection.commit()
                cursor.close()
                print(f"🔍 GENERATE PAPER DEBUG END - SUCCESS\n")
                return jsonify({'success': True, 'paper': paper, 'warnings': warnings}), 200
            
            # Chapters specified: fetch only those chapters
            print(f"ℹ️ Chapters specified; fetching questions from: {chapter_names}")
            placeholders = ','.join(['%s' for _ in chapter_names])
            query = f"SELECT * FROM questions WHERE LOWER(TRIM(subject)) = %s AND LOWER(TRIM(chapter)) IN ({placeholders})"
            chapter_params = [normalize_key(c) for c in chapter_names]
            params = [subject_norm] + chapter_params
            cursor.execute(query, params)
            all_questions = cursor.fetchall()
            
            print(f"📊 Found {len(all_questions)} questions for selected chapters")
            if all_questions:
                for q in all_questions:
                    print(f"  Q#{q['id']}: '{q['subject']}' / '{q['chapter']}' / Type: {q['question_type']} / Marks: {q['marks']}")
                type_counts = {}
                for q in all_questions:
                    qtype_norm = normalize_qtype(q.get('question_type'))
                    type_counts[qtype_norm] = type_counts.get(qtype_norm, 0) + 1
                print(f"📊 Per-type counts: {type_counts}")

            if not all_questions:
                if exam_type == 'Class Test':
                    paper = {
                        'title': f'{subject_display} Question Paper',
                        'subject': subject_display,
                        'courseCode': course_code,
                        'examType': exam_type,
                        'examTime': exam_time,
                        'total_marks': 0,
                        'questions': [],
                        'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    cursor.close()
                    return jsonify({'success': True, 'paper': paper, 'warnings': ['No questions found in selected chapters; generated empty paper']}), 200
                cursor.close()
                return jsonify({'success': False, 'message': 'No questions found for selected chapters'}), 400
            
            # ...existing code for global_dist and per_chapter_requested...
            global_dist = data.get('globalDistribution')
            desired_global_counts = {'MCQ': 0, 'One Sentence': 0, 'Long Answer': 0}
            per_chapter_requested = {}
            
            if global_dist and isinstance(global_dist, dict):
                desired_global_counts['MCQ'] = int(global_dist.get('mcq', 0) or 0)
                desired_global_counts['One Sentence'] = int(global_dist.get('oneSentence', 0) or 0)
                desired_global_counts['Long Answer'] = int(global_dist.get('longAnswer', 0) or 0)
                print(f"ℹ️ Global distribution provided: {desired_global_counts}")
            else:
                for chap_name in chapter_names:
                    d = chapter_questions_dist.get(chap_name, {})
                    desired_global_counts['MCQ'] += int(d.get('mcq', {}).get('count', 0) or 0)
                    desired_global_counts['One Sentence'] += int(d.get('oneSentence', {}).get('count', 0) or 0)
                    desired_global_counts['Long Answer'] += int(d.get('longAnswer', {}).get('count', 0) or 0)
                    per_chapter_requested[chap_name] = {'MCQ': int(d.get('mcq', {}).get('count', 0) or 0), 'One Sentence': int(d.get('oneSentence', {}).get('count', 0) or 0), 'Long Answer': int(d.get('longAnswer', {}).get('count', 0) or 0)}
                print(f"ℹ️ Per-chapter distribution: {per_chapter_requested}")
            
            selected_by_type = {'MCQ': 0, 'One Sentence': 0, 'Long Answer': 0}
            selected_questions = []
            used_ids = set()
            
            # ...existing pick_from_chapter function...
            def pick_from_chapter(chapter_qs, qtype_val, count):
                if count <= 0:
                    return []
                available = [q for q in chapter_qs if normalize_qtype(q.get('question_type')) == qtype_val and q.get('id') not in used_ids]
                remaining_global = max(0, desired_global_counts[qtype_val] - selected_by_type[qtype_val])
                take = min(count, len(available), remaining_global)
                if len(available) < count:
                    warnings.append(f"Only {len(available)} available for {qtype_val} in this chapter (requested {count})")
                if take <= 0:
                    return []
                picked = random.sample(available, take)
                print(f"  Picked {len(picked)} {qtype_val} questions")
                for q in picked:
                    used_ids.add(q.get('id'))
                    selected_by_type[qtype_val] += 1
                return picked
            
            # ...existing selection logic...
            for chap_name in chapter_names:
                chap_qs = [q for q in all_questions if normalize_key(q.get('chapter')) == normalize_key(chap_name)]
                print(f"Processing chapter '{chap_name}': {len(chap_qs)} questions available")
                
                if not chap_qs:
                    warnings.append(f"{chap_name}: no questions found in this chapter (skipping)")
                    continue
                
                per_req = per_chapter_requested.get(chap_name, None)
                if per_req is None and global_dist:
                    per_req = {'MCQ': 0, 'One Sentence': 0, 'Long Answer': 0}
                
                if per_req:
                    selected_questions.extend(pick_from_chapter(chap_qs, 'MCQ', per_req.get('MCQ', 0)))
                    selected_questions.extend(pick_from_chapter(chap_qs, 'One Sentence', per_req.get('One Sentence', 0)))
                    selected_questions.extend(pick_from_chapter(chap_qs, 'Long Answer', per_req.get('Long Answer', 0)))
            
            print(f"After first pass: {len(selected_questions)} questions selected")
            
            # ...existing second pass...
            if (desired_global_counts['MCQ'] > selected_by_type['MCQ'] or
                desired_global_counts['One Sentence'] > selected_by_type['One Sentence'] or
                desired_global_counts['Long Answer'] > selected_by_type['Long Answer']):
                print(f"Second pass: filling remaining counts...")
                type_avail_map = {'MCQ': [], 'One Sentence': [], 'Long Answer': []}
                for q in all_questions:
                    if q.get('id') in used_ids:
                        continue
                    qtype = normalize_qtype(q.get('question_type'))
                    if qtype in type_avail_map:
                        type_avail_map[qtype].append(q)
                for qtype_val in ['MCQ', 'One Sentence', 'Long Answer']:
                    while selected_by_type[qtype_val] < desired_global_counts[qtype_val] and type_avail_map[qtype_val]:
                        q = type_avail_map[qtype_val].pop(0)
                        if q.get('id') in used_ids:
                            continue
                        used_ids.add(q.get('id'))
                        selected_questions.append(q)
                        selected_by_type[qtype_val] += 1
                print(f"After second pass: {len(selected_questions)} questions selected")
            
            for t in ['MCQ', 'One Sentence', 'Long Answer']:
                if selected_by_type[t] < desired_global_counts[t]:
                    warnings.append(f"Not enough {t} in selected chapters: requested {desired_global_counts[t]}, got {selected_by_type[t]}")
            
            if not selected_questions:
                print(f"⚠️ No questions selected after filtering; using fallback...")
                fallback_pool = [q for q in all_questions if q.get('id') not in used_ids] or all_questions
                if fallback_pool:
                    selected_questions.append(random.choice(fallback_pool))
                    warnings.append('No questions matched distribution; added 1 question by fallback (from selected chapters only)')
            
            random.shuffle(selected_questions)
            actual_total_marks = sum(int(q.get('marks', 0) or 0) for q in selected_questions)
            
            print(f"✓ Final: {len(selected_questions)} questions, {actual_total_marks} marks")
            for q in selected_questions:
                print(f"  Q#{q['id']}: {q['marks']} marks")
            
            paper = {
                'title': f'{subject_display} Question Paper',
                'subject': subject_display,
                'courseCode': course_code,
                'examType': exam_type,
                'examTime': exam_time,
                'total_marks': total_marks_requested if total_marks_requested > 0 else actual_total_marks,
                'questions': selected_questions,
                'questionStructure': question_structure,
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            questions_json = json.dumps(selected_questions, default=json_serializer)
            cursor.execute('INSERT INTO papers (user_id, subject, total_marks, questions_json) VALUES (%s, %s, %s, %s)',
                          (session.get('id'), subject_display, actual_total_marks, questions_json))
            mysql.connection.commit()
            cursor.close()
            
            print(f"✓ Paper generated: {subject_display}")
            print(f"🔍 GENERATE PAPER DEBUG END - SUCCESS\n")
            return jsonify({'success': True, 'paper': paper, 'warnings': warnings}), 200
        
        except MySQLdb.Error as db_error:
            print(f"Database error: {str(db_error)}")
            print(f"🔍 GENERATE PAPER DEBUG END - DB ERROR\n")
            return jsonify({'success': False, 'message': f'Database error: {str(db_error)}'}), 500
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"🔍 GENERATE PAPER DEBUG END - ERROR\n")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/delete-question/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM questions WHERE id = %s', (question_id,))
        question = cursor.fetchone()
        
        if not question:
            cursor.close()
            return jsonify({'success': False, 'message': 'Not found'}), 404
        
        cursor.execute('DELETE FROM questions WHERE id = %s', (question_id,))
        mysql.connection.commit()
        cursor.close()
        
        print(f"✓ Deleted: {question_id}")
        return jsonify({'success': True, 'message': 'Deleted'}), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error'}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def before_request():
    if request.endpoint and request.endpoint != 'static':
        print(f"Request: {request.method} {request.path}")

def ensure_default_admin(cursor, conn):
    """Ensure there's at least one admin user and return its id."""
    cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    admin = cursor.fetchone()
    if admin:
        return admin['id']
    # Create default admin
    default_email = 'admin@local'
    default_user = 'admin'
    default_password = 'admin123'
    hashed = generate_password_hash(default_password)
    try:
        cursor.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'admin')",
                       (default_user, default_email, hashed))
        conn.commit()
        cursor.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (default_email,))
        admin = cursor.fetchone()
        if admin:
            print(f"✓ Default admin created: {default_email}")
            return admin['id']
    except Exception as e:
        print(f"Could not create default admin: {e}")
    return None

def ensure_questions_teacher_id(cursor, conn, admin_id=None):
    """
    Ensure questions table has teacher_id column, populate with admin_id for existing rows if necessary,
    and add foreign key constraint if missing.
    """
    try:
        cursor.execute("SHOW COLUMNS FROM questions LIKE 'teacher_id'")
        if cursor.fetchone() is None:
            # Add teacher_id column as nullable first
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN teacher_id INT NULL")
                conn.commit()
                print("✓ Added 'teacher_id' column to questions")
            except Exception as e:
                print(f"✗ Could not add teacher_id column: {e}")
                # don't raise - continue
        else:
            print("✓ 'teacher_id' column already exists in 'questions'")

        # If there are rows without teacher_id and we have an admin available, set them to admin_id
        if admin_id:
            try:
                cursor.execute("UPDATE questions SET teacher_id = %s WHERE teacher_id IS NULL OR teacher_id = 0", (admin_id,))
                conn.commit()
                print("✓ Updated existing questions to default admin id where missing")
            except Exception as e:
                print(f"✗ Error updating question teacher_id values: {e}")

        # Make teacher_id NOT NULL if we can (only if all rows have non-null)
        try:
            cursor.execute("SELECT COUNT(*) AS cnt FROM questions WHERE teacher_id IS NULL")
            cnt = cursor.fetchone().get('cnt', 0)
            if cnt == 0:
                try:
                    cursor.execute("ALTER TABLE questions MODIFY teacher_id INT NOT NULL")
                    conn.commit()
                    print("✓ Set 'teacher_id' column to NOT NULL")
                except Exception as e:
                    print(f"✗ Error setting teacher_id to NOT NULL: {e}")
            else:
                print(f"⚠ {cnt} questions still missing teacher_id; keeping column NULLABLE until migration is complete")
        except Exception as e:
            print(f"✗ Could not verify NULL count for teacher_id: {e}")

        # Add foreign key constraint if missing
        try:
            # Query information_schema for an existing FK on questions.teacher_id
            cursor.execute("""
                SELECT constraint_name
                FROM information_schema.key_column_usage
                WHERE table_schema = %s AND table_name = 'questions' AND column_name = 'teacher_id'
                    AND referenced_table_name = 'users'
            """, (MYSQL_DB,))
            fk_exists = cursor.fetchone()
            if not fk_exists:
                try:
                    cursor.execute("""
                        ALTER TABLE questions
                        ADD CONSTRAINT fk_questions_teacher
                        FOREIGN KEY (teacher_id) REFERENCES users(id)
                        ON DELETE CASCADE
                    """)
                    conn.commit()
                    print("✓ Added foreign key constraint: questions.teacher_id -> users.id")
                except Exception as e:
                    print(f"✗ Could not add foreign key constraint for teacher_id: {e}")
            else:
                print("✓ Foreign key constraint for questions.teacher_id already exists")
        except Exception as e:
            print(f"✗ Error while checking/adding FK constraint: {e}")

    except Exception as e:
        print(f"✗ Error in ensure_questions_teacher_id: {e}")
        # swallow to avoid breaking app startup

@app.route('/paper/<int:paper_id>')
@login_required
def view_paper(paper_id):
    """View a specific generated paper."""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM papers WHERE id = %s AND user_id = %s', (paper_id, session.get('id')))
        paper = cursor.fetchone()
        cursor.close()
        
        if not paper:
            return render_template('error.html', message='Paper not found'), 404
        
        return render_template('generated_paper.html', paper=paper)
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template('error.html', message=f'Error: {str(e)}'), 500

if __name__ == '__main__':
    print("Starting Paper Generator...")
    print("Initializing database...")
    if init_db():
        print("✓ Database initialized successfully!")
        print("✓ Ready!")
        print("Running on http://localhost:5000")
        app.run(debug=True, host='localhost', port=5000)
    else:
        print("✗ Init failed!")
