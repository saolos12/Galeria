# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Credenciales simples
USERS = {'grupo_trabajo': '1234'}

# Obtener la URL de la base de datos desde el entorno de Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("No se encontró la variable de entorno DATABASE_URL. Asegúrate de configurarla en Render.")

def get_db_conn():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Inicializa la base de datos una sola vez al inicio
with get_db_conn() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE  table_name   = 'images'
        );
    """)
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        init_db()
    cursor.close()


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if USERS.get(username) == password:
            return redirect(url_for('gallery'))
        return "Usuario o contraseña incorrectos", 401
    return render_template('login.html')

@app.route('/gallery', methods=['GET'])
def gallery():
    with get_db_conn() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM images ORDER BY id DESC')
        images = cursor.fetchall()
        cursor.close()
    return render_template('gallery.html', images=images)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No se encontró el archivo'})
    
    file = request.files['file']
    title = request.form.get('title', 'Sin título')

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'})

    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        try:
            with get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO images (title, filename) VALUES (%s, %s)', (title, filename))
                conn.commit()
                cursor.close()
            return jsonify({'success': True, 'message': 'Imagen subida exitosamente'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error al subir la imagen: {e}'})
    
    return jsonify({'success': False, 'message': 'Error al subir la imagen'})

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)