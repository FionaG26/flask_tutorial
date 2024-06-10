import os
from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db
import json

bp = Blueprint('blog', __name__, template_folder='templates')


@bp.route('/home')
def home():
    return render_template('base.html')


@bp.route('/')
def index():
    db = get_db()
    # Fetch articles that are published (i.e., publish_date is not null and before or equal to the current datetime)
    posts = db.execute(
        'SELECT p.id, title, summary, created, author_id, username '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'WHERE publish_date IS NOT NULL AND publish_date <= ? ' 
        'ORDER BY created DESC',
        (datetime.now(),)
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

        if publish_date:
            try:
                publish_datetime = datetime.strptime(publish_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                error = 'Invalid date format for publish date. Use YYYY-MM-DDTHH:MM.'
                flash(error)
        else:
            image_url = None
            if image and image.filename != '':
                uploads_dir = os.path.join(bp.root_path, 'static/uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)

                filename = secure_filename(image.filename)
                image_path = os.path.join(uploads_dir, filename)
                image.save(image_path)
                image_url = f'uploads/{filename}'

            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, summary, image, category, tags, publish_date, seo_title, seo_description, seo_keywords, author_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title,
                 body,
                 summary,
                 image_url,
                 category,
                 tags,
                 publish_datetime,
                 seo_title,
                 seo_description,
                 seo_keywords,
                 g.user['id']))
            db.commit()
            article_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            return redirect(url_for('blog.article', article_id=article_id))
    return render_template('blog/index.html')


@bp.route('/autosave', methods=['POST'])
def autosave():
    data = request.form.to_dict()
    with open('draft.json', 'w') as f:
        json.dump(data, f)
    return jsonify({'status': 'success'})


@bp.route('/article/<int:article_id>')
def article(article_id):
    db = get_db()
    article = db.execute(
        'SELECT id, title, body, summary, image, category, tags, publish_date, seo_title, seo_description, seo_keywords, created, author_id '
        'FROM post WHERE id = ?', (article_id,)
    ).fetchone()

    if article is None:
        flash('Article not found')
        return redirect(url_for('blog.index'))

    return render_template('blog/view.html', article=article)


@bp.route('/preview', methods=['POST'])
def preview():
    data = request.form.to_dict()
    return render_template('blog/preview.html', data=data)


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'WHERE p.id = ?',
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

        if publish_date:
            try:
                publish_datetime = datetime.strptime(publish_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                error = 'Invalid date format for publish date. Use YYYY-MM-DDTHH:MM.'
                flash(error)
        else:
            image_url = post['image']
            if image and image.filename != '':
                uploads_dir = os.path.join(bp.root_path, 'static/uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)

                filename = secure_filename(image.filename)
                image_path = os.path.join(uploads_dir, filename)
                image.save(image_path)
                image_url = f'uploads/{filename}'

            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, summary = ?, image = ?, category = ?, tags = ?, publish_date = ?, seo_title = ?, seo_description = ?, seo_keywords = ?'
                'WHERE id = ?',
                (title,
                 body,
                 summary,
                 image_url,
                 category,
                 tags,
                 publish_datetime,
                 seo_title,
                 seo_description,
                 seo_keywords,
                 id))
            db.commit()
            return redirect(url_for('blog.article', article_id=id))
    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
