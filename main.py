from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date

from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, CreateUserForm, CreateLoginForm, CreateCommentForm
from flask_gravatar import Gravatar
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

##ADD AND CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.app_context().push()

Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

##CONFIGURE TABLES

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

    # This will act like a List of Comment objects attached to each User.
    # The "comment_author" refers to the author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")



class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # ***************Child Relationship*************#
    # Create Foreign Key, "users.id" the users refers to the table name of User.
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    # author = db.Column(db.String(250), nullable=False)

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    #***************Parent Relationship*************#
    # This will act like a List of Comment objects attached to each User.
    # The "parent_post" refers to the author property in the Comment class.
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    #***************Child Relationship*************#

    # Create Foreign Key, "users.id" the users refers to the table name of User.
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    comment_author = relationship("User", back_populates="comments")

    # Create Foreign Key, "blog_posts.id" the blog_posts refers to the table name of BlogPost.
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    # Create reference to the BlobPost object, the "comments" refers to the comments property in the BlogPost class.
    parent_post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.Text, nullable=False)


db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated == False or current_user.id != 1:
            # return redirect(url_for('get_all_posts'))
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function



@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = CreateUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email = form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        new_user = User(
            email=form.email.data,
            password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8),
            name=form.name.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = CreateLoginForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user_password = form.password.data
        user = User.query.filter_by(email = user_email).first()

        try:
            if user.email == user_email and check_password_hash(user.password, user_password):
                login_user(user)
                return redirect(url_for("get_all_posts"))
        except AttributeError:
            flash('Password incorrect. Please try again.')
            return render_template("login.html", logged_in=current_user.is_authenticated)


    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("get_all_posts"))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    comment_form = CreateCommentForm()
    requested_post = BlogPost.query.get(post_id)

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You are not logged in !!")
            return redirect(url_for("login"))

        new_comment = Comment(text=comment_form.body.data, author_id=current_user.id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        comment_form.body.data = ""
    return render_template("post.html", form=comment_form, post=requested_post, current_user=current_user, logged_in=current_user.is_authenticated)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
