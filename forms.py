from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CreateUserForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired()])
    password = StringField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class CreateLoginForm(FlaskForm):
    email = StringField("email", validators=[DataRequired()])
    password = StringField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class CreateCommentForm(FlaskForm):
    body = CKEditorField("comment_text", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
