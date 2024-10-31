from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL  
from werkzeug.security import generate_password_hash
import logging
import os
import bcrypt
from flask import session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = '4534789265' 

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' 
app.config['MYSQL_DB'] = 'sgmbe'
app.config['UPLOAD_FOLDER'] = 'static/upload_floder'



mysql = MySQL(app)  
logging.basicConfig(level=logging.DEBUG)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    cur.close()
    return render_template('user_dashboard.html', products=data)

@app.route('/logout', methods=['POST', 'GET'])  # Added methods here
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('login'))  # Redirect to the login page




@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        details = request.form
        fname = details.get('fullname')
        address = details.get('address')
        contact = details.get('mobileno')
        dob = details.get('date')
        emailid = details.get('email')
        password = details.get('password')
        gender = details.get('gender') 

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO signup (full_name, address, contact, email, dob, password, gender) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (fname, address, contact, emailid, dob, password, gender)
            )
            mysql.connection.commit()
            return "Record Inserted"
        except Exception as e:
            mysql.connection.rollback()
            app.logger.error(f"An error occurred: {e}")
            return f"An error occurred: {e}"
        finally:
            cur.close()
    return render_template('signup.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        details = request.form
        email = details['email']
        password = details['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM signup WHERE email=%s AND password=%s", (email, password))
        data = cur.fetchone()
        if data:
            session['user_id'] = data[0]
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM signup WHERE email=%s", (email,))
        user = cur.fetchone()
        
        if user:
            # Redirect to the reset password page with the user's email
            return redirect(url_for('reset_password', email=email))
        else:
            flash("Email not found in our records.", "error")
        
        cur.close()

    return render_template('forgot_password.html')


@app.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE signup SET password=%s WHERE email=%s", (new_password, email))
        mysql.connection.commit()
        flash("Your password has been updated successfully. You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html', email=email)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect if not logged in

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        # Update user information
        details = request.form
        fname = details.get('fullname')
        address = details.get('address')
        contact = details.get('mobileno')
        dob = details.get('date')
        emailid = details.get('email')
        gender = details.get('gender')

        try:
            cur.execute(
                "UPDATE signup SET full_name=%s, address=%s, contact=%s, email=%s, dob=%s, gender=%s WHERE id=%s",
                (fname, address, contact, emailid, dob, gender, user_id)
            )
            mysql.connection.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            mysql.connection.rollback()
            app.logger.error(f"An error occurred: {e}")
            flash("An error occurred while updating the profile.", "error")

    # Retrieve user data
    cur.execute("SELECT * FROM signup WHERE id=%s", (user_id,))
    user_data = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user_data)







# Route to view a single product
@app.route('/product/<int:product_id>')
def product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product_data = cur.fetchone()
    cur.close()

    if product_data:
        return render_template('product_page.html', 
                               product_name=product_data[1],
                               price=product_data[3],
                               description=product_data[4],
                               category=product_data[2],
                               quantity=product_data[5],
                               image_path=product_data[6])
    else:
        return "Product not found", 404

# Route to list all products
@app.route('/products', methods=['GET'])
def list_products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()

    return render_template('product_list.html', products=products)



    
@app.route('/buy', methods=['POST', 'GET'])
def buy():
    if request.method == 'POST':
        # Handle form submission
        name = request.form['name']
        email = request.form['email']
        product_name = request.form['product_name']
        price = request.form['price']
        quantity = request.form['quantity']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO purchases (name, email, product_name, price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, product_name, price, quantity))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('feedback'))
       
    else:
        # If GET, render the purchase form with the parameters
        product_name = request.args.get('product_name')
        price = request.args.get('price')
        quantity = request.args.get('quantity')
        return render_template('buy_form.html', product_name=product_name, price=price, quantity=quantity)

@app.route('/feedback', methods=['POST', 'GET'])
def feedback():
    if request.method == "POST":
        details = request.form
        fname = details.get('fullname')
        emailid = details.get('email')
        contact = details.get('contact')
        date = details.get('date')
        message = details.get('message')
        app.logger.debug(f"Received form data: {details}")
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO feedback (full_name, email, contact, date, message) VALUES (%s, %s, %s, %s, %s)",
                (fname, emailid, contact, date, message)
            )
            mysql.connection.commit()
            return "Record Inserted"
        except Exception as e:
            mysql.connection.rollback()
            app.logger.error(f"An error occurred: {e}")
            return f"An error occurred: {e}"
        finally:
            cur.close()
    return render_template('feedback.html')  # Ensure 'feedback.html' is the correct template name

@app.route('/home')
def home():
    try:
        # Redirect to the product list instead of rendering home.html
        return redirect(url_for('list_products'))  # Ensure 'list_products' is the correct endpoint
    except Exception as e:
        return str(e)




if __name__ == "__main__":
    app.run(debug=True)
    





