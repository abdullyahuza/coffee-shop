import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# db_drop_and_create_all()

# check if drink already exist


def itExist(title):
    _query = Drink.query.filter_by(title=title).first()
    if _query is None:
        return False
    return True


######################
    # ROUTES
######################

# get drinks
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.short() for drink in drinks]
    except BaseException:
        abort(422)

    response_dic = {
        "success": True,
        "drinks": formatted_drinks
    }

    return jsonify(response_dic), 200


# get drink details
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in drinks]

    except BaseException:
        abort(422)

    response_dic = {
        'success': True,
        'drinks': formatted_drinks
    }

    return jsonify(response_dic), 200


# post a drink
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_a_drink(payload):

    new_title = request.get_json()['title']
    new_recipe = json.dumps(request.get_json()['recipe'])

    if not new_title or not new_recipe:
        abort(400)
    elif itExist(new_title):
        abort(409)
    else:
        try:
            drink = Drink(title=new_title, recipe=new_recipe)
            drink.insert()

            inserted_drink = Drink.query.filter_by(title=new_title).first()
            response_dic = {
                "success": True,
                "drinks": inserted_drink.long()
            }
            return jsonify(response_dic), 200
        except BaseException:
            abort(422)


# Patch a drink
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_a_drink(payload, drink_id):
    new_title = request.get_json().get('title')
    new_recipe = request.get_json().get('recipe')
    drink = Drink.query.get(drink_id)

    if not new_title and not new_recipe:
        abort(400)
    elif not drink:
        abort(404)
    else:
        try:
            if new_title:
                drink.title = new_title
            if new_recipe:
                drink.recipe = json.dumps(new_recipe)

            drink.update()

            response_dic = {
                "success": True,
                "drinks": [drink.long()]
            }

            return jsonify(response_dic), 200
        except BaseException:
            abort(422)


# Delete a drink
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_a_drink(payload, drink_id):

    drink = Drink.query.get(drink_id)

    if not drink:
        abort(404)
    else:
        try:

            drink.delete()

            response_dic = {
                "success": True,
                "delete": drink_id
            }

            return jsonify(response_dic), 200
        except BaseException:
            abort(422)

# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(409)
def duplicate(error):
    return jsonify({
        "success": False,
        "error": 409,
        "message": "conflict"
    }), 409


@app.errorhandler(404)
def not_found(error):
    return({
        "success": False,
        "message": "resource not found",
        "error": 404
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return({
        "success": False,
        "message": "bad request",
        "error": 400
    }), 400


@app.errorhandler(405)
def not_found(error):
    return (jsonify({"success": False, "error": 405,
                     "message": "method not allowed"}), 405)


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
    }), 500


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code
