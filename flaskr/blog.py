import os
from flask import Flask
from . import db
from . import auth, blog

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app


from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
import os
import json

bp = Blueprint('blog', __name__)

@bp.route('/home')
def home():
    return render_template('base.html')
    

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        summary = request.form.get('summary')
        image = request.files.get('image')
        category = request.form.get('category')
        tags = request.form.get('tags')
        publish_date = request.form.get('publish_date')
        seo_title = request.form.get('seo_title')
        seo_description = request.form.get('seo_description')
        seo_keywords = request.form.get('seo_keywords')
        error = None

        if not title:
            error = 'Title is required.'
        if not body:
            error = 'Body is required.'

        if error is not None:
            flash(error)
        else:
            if image and image.filename != '':
                image_path = os.path.join('static/uploads', image.filename)
                image.save(image_path)
                image_url = f'uploads/{image.filename}'
            else:
                image_url = None

            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, summary, image, category, tags, publish_date, seo_title, seo_description, seo_keywords, author_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title, body, summary, image_url, category, tags, publish_date, seo_title, seo_description, seo_keywords, g.user['id'])
            )
            db.commit()
            article_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            return redirect(url_for('blog.article', article_id=article_id))

    return render_template('blog/create.html')

# Autosave route
@bp.route('/autosave', methods=['POST'])
def autosave():
    data = request.form.to_dict()
    with open('draft.json', 'w') as f:
        json.dump(data, f)
    return jsonify({'status': 'success'})

# Route for individual article view
@bp.route('/article/<int:article_id>')
def article(article_id):
    db = get_db()
    article = db.execute(
        'SELECT * FROM post WHERE id = ?',
        (article_id,)
    ).fetchone()
    
    if article is None:
        flash('Article not found')
        return redirect(url_for('blog.home'))

    return render_template('blog/article.html', article=article)


@bp.route('/preview', methods=['POST'])
def preview():
    data = request.form.to_dict()
    return render_template('blog/preview.html', data=data)

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>', methods=('GET',))
def view(id):
    post = get_post(id)
    return render_template('blog/view.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
