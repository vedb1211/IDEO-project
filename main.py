from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_BINDS'] = {'posts': 'sqlite:///post.db'}

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

now = datetime.now()

svg = ['static/assets/avatar-svgrepo-com (0).svg', 'static/assets/avatar-svgrepo-com (1).svg', 'static/assets/avatar-svgrepo-com (2).svg']

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    svg = db.Column(db.String(100), nullable=False)


class Post(db.Model):
    __tablename__ = 'posts'  # Explicitly define table name if necessary


    # __bind_key__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    svg = db.Column(db.String(100), nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.String(500), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

# new_comment = Comment(text='Your comment text here', post_id=1)  # Replace with the actual post_id


with app.app_context():
    db.create_all()


@app.route('/')
def page():
    return render_template("home.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hash_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=2)
        new_user = User(email=request.form.get('email'), password=hash_password, name=request.form.get('name'), svg=random.choice(svg))
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html")


@app.route("/home", methods=["GET", "POST"])
# ...

@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        search_query = request.form.get('search_query')

        # Filter posts based on title and author
        filtered_posts = Post.query.filter(
            db.or_(Post.title.ilike(f"%{search_query}%"), Post.author.ilike(f"%{search_query}%"))
        ).all()

        return render_template('index.html', all_post=filtered_posts, search_query=search_query)

    result = db.session.execute(db.select(Post))
    posts = result.scalars().all()
    return render_template('index.html', all_post=posts, search_query=None)  # Provide a default value for search_query

# ...

@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    description = request.form.get('description')

    if title and description:
        new_post = Post(title=title, description=description, date=now.strftime("%H:%M, %d %B"), author=current_user.name, svg=current_user.svg)
        db.session.add(new_post)
        db.session.commit()

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('page'))

# Route to handle upvotes
@app.route('/upvote/<int:post_id>')
def upvote(post_id):
    post = Post.query.get_or_404(post_id)
    post.upvotes += 1
    db.session.commit()
    # Redirect back to the post or home page

# Route to display comments for a post

# Route to display comments for a post
@app.route('/comments/<int:post_id>')
def show_comments(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('comments.html', post=post, comments=comments, post_id=post_id)

@app.route('/add_comment', methods=['POST'])
def add_comment():
    comment_text = request.form.get('comment_body')
    post_id_str = request.form.get('post_id')
    print(f"Received post_id: {post_id_str} and comment: {comment_text}")

    try:
        post_id = int(post_id_str)
    except (TypeError, ValueError):
        print(f"Error converting post_id: {post_id_str}")
        return redirect(url_for('home'))

    new_comment = Comment(text=comment_text, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()

    return redirect(url_for('show_comments', post_id=post_id))







if __name__ == '__main__':
    app.run(debug=True)
