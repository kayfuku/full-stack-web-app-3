import os
from flask import Flask, request, jsonify, abort, flash
import traceback
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"*": {'origins': r"*"}})

# CORS Headers


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origions', '*')  # ?
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET, POST, PATCH, DELETE, OPTIONS')
    return response


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.order_by(Drink.id).all()
    # if len(drinks) == 0:
    #     abort(404)

    formatted_drinks = [drink.short() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = Drink.query.order_by(Drink.id).all()
    # if len(drinks) == 0:
    #     abort(404)

    formatted_drinks = [drink.long() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    body = request.get_json()
    print('body:', body)

    if body is None:
        abort(400)

    try:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)
        # print('new_title:', new_title)
        # print(type(new_recipe))
        # print('new_recipe:', str(new_recipe))
        # print(type(json.dumps(new_recipe)))

        # Make sure that the user entered both the title and the recipe.
        if new_title is None or new_recipe is None:
            abort(400)

        # Build the new drink object and add it to the database.
        # json.dumps() converts list to string.
        new_drink = Drink(title=new_title, recipe=json.dumps(new_recipe))
        new_drink.insert()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        })

    except Exception as ex:
        flash('An error occurred. New drink could not be created.')
        db.session.rollback()
        abort(422)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
    print('drink_id:', drink_id)
    body = request.get_json()

    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        return jsonify({
            'success': False,
            'error': 'Drink id ' + drink_id + ' not found to be edited.'
        }), 404

    else:
        try:
            new_title = body.get('title', None)
            new_recipe = body.get('recipe', None)

            drink.title = new_title or drink.title
            drink.recipe = json.dumps(new_recipe) or drink.recipe

            drink.update()

            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            })

        except Exception as ex:
            flash('An error occurred. Drink id ' + drink_id +
                  ' could not be updated.')
            db.session.rollback()
            abort(422)


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        return jsonify({
            'success': False,
            'error': 'Drink id ' + drink_id + ' not found to be deleted.'
        }), 404

    else:
        try:
            drink.delete()

            return jsonify({
                'success': True,
                'id': drink_id
            })

        except Exception as ex:
            flash(
                'An error occurred. Drink id ' + drink_id +
                ' could not be deleted.')
            db.session.rollback()
            traceback.print_exc()
            abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def process_AuthError(error):
    response = jsonify(error.error)
    response.status_code = error.status_code

    return response
