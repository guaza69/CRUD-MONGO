from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'Guaza2025'  # Cambia esto por una clave más segura en producción

# Configuración de CSRF
csrf = CSRFProtect(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Conexión MySQL
def get_db():
    try:
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='moda_db',
            autocommit=False
        )
        return db
    except Error as e:
        flash('Error de conexión con la base de datos', 'error')
        print(f"Error MySQL: {e}")
        return None

# Modelo de Usuario
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    if db:
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return User(user['id']) if user else None
        except Error as e:
            print(f"Error al cargar usuario: {e}")
            return None
        finally:
            cursor.close()
            db.close()
    return None

# Rutas principales
@app.route('/')
@login_required
def index():
    try:
        db = get_db()
        if db is None:
            return render_template('index.html', productos=[])
            
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        return render_template('index.html', productos=productos)
    except Error as e:
        flash(f'Error al cargar productos: {str(e)}', 'error')
        return render_template('index.html', productos=[])
    finally:
        cursor.close()
        db.close()

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        # Verifica si todos los campos requeridos están presentes
        required_fields = ['nombre', 'descripcion', 'precio', 'talla', 'color']
        if not all(field in request.form for field in required_fields):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('add_product'))  # Redirige al formulario

        # Conexión a la base de datos
        db = get_db()
        if db is None:
            flash('Error al conectar con la base de datos', 'error')
            return redirect(url_for('index'))  # Redirige al índice si hay error de conexión

        cursor = db.cursor()
        try:
            # Inserta datos en la base de datos
            cursor.execute(
                "INSERT INTO productos (nombre, descripcion, precio, talla, color) VALUES (%s, %s, %s, %s, %s)",
                (request.form['nombre'], request.form['descripcion'], 
                 float(request.form['precio']), request.form['talla'], 
                 request.form['color'])
            )
            db.commit()
            flash('Producto añadido correctamente', 'success')
        except Error as e:
            db.rollback()
            flash(f'Error al añadir producto: {str(e)}', 'error')
        finally:
            cursor.close()
            db.close()

        return redirect(url_for('index'))  # Redirige después de guardar

    # Maneja la solicitud GET (formulario vacío)
    producto = {
        'nombre': '',
        'descripcion': '',
        'precio': '',
        'talla': '',
        'color': ''
    }
    return render_template('add_product.html', producto=producto)

@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if request.method == 'POST':
        db = get_db()
        if db is None:
            return redirect(url_for('index'))
            
        cursor = db.cursor()
        try:
            cursor.execute(
                """UPDATE productos SET 
                    nombre = %s, 
                    descripcion = %s, 
                    precio = %s, 
                    talla = %s, 
                    color = %s 
                WHERE id = %s""",
                (request.form['nombre'], request.form['descripcion'],
                 float(request.form['precio']), request.form['talla'],
                 request.form['color'], product_id)
            )
            db.commit()
            flash('Producto actualizado correctamente', 'success')
        except Error as e:
            db.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'error')
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('index'))
    
    db = get_db()
    if db is None:
        return redirect(url_for('index'))
        
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM productos WHERE id = %s", (product_id,))
        producto = cursor.fetchone()
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('index'))
        return render_template('edit_product.html', producto=producto)
    except Error as e:
        flash(f'Error al cargar producto: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        db.close()

@app.route('/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    db = get_db()
    if db is None:
        return redirect(url_for('index'))
        
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM productos WHERE id = %s", (product_id,))
        db.commit()
        flash('Producto eliminado correctamente', 'success')
    except Error as e:
        db.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'error')
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Usuario y contraseña son obligatorios', 'error')
            return redirect(url_for('login'))

        db = get_db()
        if db is None:
            return redirect(url_for('login'))
            
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id FROM usuarios WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            if user:
                user_obj = User(user['id'])
                login_user(user_obj)
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrectos', 'error')
        except Error as e:
            flash(f'Error de base de datos: {str(e)}', 'error')
        finally:
            cursor.close()
            db.close()
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

#Prueba    
