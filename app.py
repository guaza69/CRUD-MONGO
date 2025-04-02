from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'admin123'  

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Ruta para redirigir si el usuario no está autenticado

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['moda_db']
collection = db['productos']
users_collection = db['usuarios']  # Colección para almacenar usuarios

# Modelo de usuario
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Cargar usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        return User(str(user['_id']))
    return None

# Ruta de registro (nueva)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verificar si el usuario ya existe
        if users_collection.find_one({'username': username}):
            flash('El nombre de usuario ya está en uso', 'error')
            return redirect(url_for('register'))
        
        # Crear el nuevo usuario (sin hashing)
        user = {
            'username': username,
            'password': password  # Almacena la contraseña en texto plano
        }
        users_collection.insert_one(user)
        
        flash('Registro exitoso. Inicia sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Buscar el usuario en la base de datos
        user = users_collection.find_one({'username': username})
        if user and user['password'] == password:  # Compara contraseñas directamente
            user_obj = User(str(user['_id']))
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Ruta principal (protegida)
@app.route('/')
@login_required
def index():
    productos = list(collection.find())
    return render_template('index.html', productos=productos)

# Ruta para agregar un producto (protegida)
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        talla = request.form['talla']
        color = request.form['color']
        
        producto = {
            'nombre': nombre,
            'descripcion': descripcion,
            'precio': precio,
            'talla': talla,
            'color': color
        }
        
        collection.insert_one(producto)
        flash('Producto agregado exitosamente', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_product.html')

# Ruta para editar un producto (protegida)
@app.route('/edit/<string:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    producto = collection.find_one({'_id': ObjectId(product_id)})
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        talla = request.form['talla']
        color = request.form['color']
        
        collection.update_one({'_id': ObjectId(product_id)}, {'$set': {
            'nombre': nombre,
            'descripcion': descripcion,
            'precio': precio,
            'talla': talla,
            'color': color
        }})
        
        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', producto=producto)

# Ruta para eliminar un producto (protegida)
@app.route('/delete/<string:product_id>')
@login_required
def delete_product(product_id):
    collection.delete_one({'_id': ObjectId(product_id)})
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 
    #Prueba 
    