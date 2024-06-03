# tests/test_blog.py

import pytest
from flaskr.db import get_db
from flaskr import create_app


def test_index(client, auth):
    response = client.get('/')
    assert b"Log In" in response.data
    auth.login()
    response = client.get('/')
    assert b"Log Out" in response.data
    assert b'test title' in response.data
    assert b'by test on 2023-01-01' in response.data
    assert b'test\nbody' in response.data


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


def test_author_required(app, client, auth):
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    response = client.post('/1/update')
    assert response.status_code == 403
    response = client.post('/1/delete')
    assert response.status_code == 403


@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    response = client.post(path)
    assert response.status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    response = client.post('/create', data={'title': 'created', 'body': ''})
    assert response.headers['Location'] == '/'

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/update').status_code == 200
    response = client.post('/1/update', data={'title': 'updated', 'body': ''})
    assert response.headers['Location'] == '/'

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers['Location'] == '/'

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None
