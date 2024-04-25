from flask import Flask, flash, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from flask import request


app = Flask(__name__)
app.secret_key = '22771d8a39fd4fca1531468593ff6006'


# PostgreSQL connection parameters
db_params = {
    'dbname': 'cmsdb',
    'user': 'postgres',
    'password': 'Alsen#211',
    'host': 'host.docker.internal', 
    'port': 5432, 
}

con = psycopg2.connect(**db_params)
print(con)
conn = con.cursor()


# Database setup
conn.execute('CREATE TABLE IF NOT EXISTS USERS(ID SERIAL PRIMARY KEY, USERNAME TEXT, PASSWORD TEXT, IS_ADMIN BOOLEAN DEFAULT FALSE, IS_DELETED BOOLEAN DEFAULT FALSE)')
conn.execute('CREATE TABLE IF NOT EXISTS ARTICLES(ID SERIAL PRIMARY KEY, TITLE TEXT, CONTENT TEXT, AUTHOR_ID INTEGER REFERENCES USERS(ID))')
conn.execute('CREATE TABLE IF NOT EXISTS COMMENTS(ID SERIAL PRIMARY KEY, TITLE TEXT, CONTENT TEXT, AUTHOR_ID INTEGER REFERENCES USERS(ID))')

print("here")
conn.close()

@app.route('/admin_users')
def admin_users():
    try:
        con = psycopg2.connect(**db_params)
        cursor = con.cursor()
        cursor.execute('SELECT ID, USERNAME FROM "users" WHERE IS_ADMIN = false AND is_deleted = FALSE')
        non_deleted_users = cursor.fetchall()
        con.close()

        return render_template('admin_users.html', non_deleted_users=non_deleted_users)

    except psycopg2.Error as e:
        return f"An error occurred while fetching non-deleted users: {e}"


@app.route('/confirm_delete/<int:user_id>', methods=['POST'])
def confirm_delete(user_id):
    if request.method == 'POST':
        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('UPDATE "users" SET is_deleted = TRUE WHERE id = %s', (user_id,))
            con.commit()
            con.close()
            return redirect(url_for('admin_users'))
        except psycopg2.Error as e:
            return f"An error occurred while deleting the user: {e}"
    return redirect(url_for('admin_users'))



@app.route('/recover_users', methods=['GET', 'POST'])
def recover_users():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username and password match a deleted user in the database
        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('SELECT ID, PASSWORD FROM "users" WHERE USERNAME = %s AND is_deleted = true', (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[1], password):
                # If the username and password match, recover the user by setting is_deleted to false
                cursor.execute('UPDATE "users" SET is_deleted = false WHERE ID = %s', (user[0],))
                con.commit()
                con.close()
                return redirect(url_for('signin'))  # Redirect to admin users page or any other appropriate page
            else:
                # If username or password is incorrect, display an error message
                flash('Invalid username or password. Please try again.', 'error')
                return render_template('recover_users.html')
        except psycopg2.Error as e:
            return f"An error occurred while recovering user: {e}"

    else:
        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('SELECT ID, USERNAME FROM "users" WHERE is_deleted = true')  # Fetch deleted users
            deleted_users = cursor.fetchall()
            con.close()

            return render_template('recover_users.html', deleted_users=deleted_users)

        except psycopg2.Error as e:
            return f"An error occurred while fetching deleted users: {e}"


@app.route('/')
def home():
    return render_template('dashboard.html')



@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    user_id = session.get('user_id')
    if username:
        return render_template('dashboard.html', username=username,user_id=user_id)
    else:
        return redirect(url_for('signin'))


from flask import redirect

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['psw']

        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('SELECT * FROM USERS WHERE USERNAME = %s AND is_deleted = FALSE', (username,))
            user = cursor.fetchone()
            con.close()

            if user and check_password_hash(user[2], password):
                session['username'] = user[1]
                session['user_id'] = user[0]
                # Check if the user is an admin
                if user[3]:  # Assuming the 4th column in the USERS table indicates admin status
                    return redirect(url_for('admin_users'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                # Display an error message using flash
                flash('Invalid username or password. Please try again.', 'error')
                return render_template('signin.html')

        except psycopg2.Error as e:
            return f"Database error: {e}"

    return render_template('signin.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['psw']

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()

            # Check if the username already exists
            cursor.execute('SELECT COUNT(*) FROM "users" WHERE USERNAME = %s', (username,))
            user_count = cursor.fetchone()[0]

            if user_count > 0:
                # Username already exists, show an error message on the front end
                flash("Username already exists. Please choose another username.", "error")
                return render_template('signup.html')

            # Insert the new user into the database
            cursor.execute('INSERT INTO "users" (USERNAME, PASSWORD) VALUES (%s, %s)', (username, hashed_password))
            con.commit()
            con.close()

            return redirect(url_for('signin'))

        except psycopg2.Error as e:
            return f"An error occurred during signup. Error details: {e}"

    return render_template('signup.html')




@app.route('/signout', methods=['GET', 'POST'])
def signout():
    session.clear()
    return render_template('dashboard.html')


@app.route('/view_article')
def view_article():
    username = session.get('username')
    if username:
        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('SELECT ID FROM USERS WHERE USERNAME = %s', (username,))
            user_id = cursor.fetchone()[0]
            cursor.execute('SELECT ID, TITLE, CONTENT FROM ARTICLES WHERE AUTHOR_ID = %s', (user_id,))
            articles = cursor.fetchall()
            print(articles)
            con.close()

            return render_template('view_article.html', articles=articles, username=username)
        except psycopg2.Error as e:
            return f"An error occurred while fetching articles: {e}"

    else:
        return redirect(url_for('signin'))


@app.route('/add_article', methods=['GET', 'POST'])
def add_article():
    username=session.get('username')
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        username = session.get('username')

        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('SELECT ID FROM USERS WHERE USERNAME = %s', (username,))
            user_id = cursor.fetchone()[0]
            cursor.execute('INSERT INTO "articles" (TITLE, CONTENT, AUTHOR_ID) VALUES (%s, %s, %s)', (title, content, user_id))
            con.commit()
            con.close()

            return redirect(url_for('view_article',username=username))

        except psycopg2.Error as e:
            return f"An error occurred during article addition. Error details: {e}"

    return render_template('add_article.html',username=username)


def get_article_by_id(article_id):
    try:
        con = psycopg2.connect(**db_params)
        cursor = con.cursor()
        cursor.execute('SELECT ID, TITLE, CONTENT FROM "articles" WHERE ID = %s', (article_id,))
        article = cursor.fetchone()
        con.close()
        return article
    except psycopg2.Error as e:
        return None

@app.route('/edit_article/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    if request.method == 'POST':
        new_title = request.form['new_title']
        new_content = request.form['new_content']

        try:
            con = psycopg2.connect(**db_params)
            cursor = con.cursor()
            cursor.execute('UPDATE "articles" SET TITLE = %s, CONTENT = %s WHERE ID = %s', (new_title, new_content, article_id))
            con.commit()
            con.close()

            return redirect(url_for('view_article'))

        except psycopg2.Error as e:
            return f"An error occurred during article update. Error details: {e}"

    # Fetch article data (replace with your actual data retrieval logic)
    article = get_article_by_id(article_id)
    username = session.get('username')

    if article:
        return render_template('edit_article.html', article=article,username=username)
    else:
        return "Article not found"  # Handle case when article is not found


@app.route('/delete_article/<int:article_id>', methods=['POST'])
def delete_article(article_id):
    con = psycopg2.connect(**db_params)
    cursor = con.cursor()
    cursor.execute('DELETE FROM "articles" WHERE ID = %s', (article_id,))
    con.commit()
    con.close()
    return redirect(url_for('view_article'))

@app.route('/delete_account/<int:user_id>', methods=['POST','GET'])
def delete_account(user_id):
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verify username and password
        if verify_credentials(username, password):
            try:
                con = psycopg2.connect(**db_params)
                cursor = con.cursor()
                cursor.execute('UPDATE "users" SET is_deleted = TRUE WHERE id = %s', (user_id,))
                con.commit()
                con.close()
                return redirect(url_for('signin'))
            except psycopg2.Error as e:
                return f"An error occurred while deleting the user: {e}"
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('delete_account', user_id=user_id))  # Redirect to delete_account with user_id
    return render_template('delete_account.html',user_id=user_id)



def verify_credentials(username, password):
    try:
        con = psycopg2.connect(**db_params)
        cursor = con.cursor()
        cursor.execute('SELECT PASSWORD FROM "users" WHERE USERNAME = %s AND is_deleted = FALSE', (username,))
        user_password = cursor.fetchone()
        con.close()

        if user_password and check_password_hash(user_password[0], password):
            return True
        else:
            return False
    except psycopg2.Error as e:
        return False  # Return False if any database error occurs



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
