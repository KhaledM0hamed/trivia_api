import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

# from backend.models import Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins.
    Delete the sample route after completing the TODOs
    # Done
    '''
    cors = CORS(app, resources={r"/api/*": {"origin": "*"}})
    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    # Done
    '''

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    '''
    @TODO:
    # Done
    Create an endpoint to handle GET requests
    for all available categories.
    '''

    @app.route("/categories", methods=['GET'])
    def get_categories():
        query = Category.query.all()
        categories = list(map(Category.format, query))
        return jsonify({
            "success": True,
            "categories": categories
        })

    '''
  @TODO:
  # Done
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at
  the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''

    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        selected_questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selected_questions)
        query = Category.query.all()
        categories = list(map(Category.format, query))

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'questions': current_questions,
            'total_questions': len(query),
            'categories': categories,
            'current_category': None,
            'success': True
        })

    '''
  @TODO:
  # Done
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question,
  the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).first()
            question.delete()

            return jsonify({
                'deleted': question_id,
                'success': True
            })

        except Exception:
            abort(422)

    '''
  @TODO:
  # Done
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

    @app.route("/questions", methods=['POST'])
    def add_question():
        body = request.get_json(force=True)

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        try:

            question = Question(question=new_question,
                                answer=new_answer,
                                category=new_category,
                                difficulty=new_difficulty)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id,
                'total_questions': len(Question.query.all())
            })

        except Exception:
            abort(422)

    '''
  @TODO:
  # Done
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''

    @app.route("/searchQuestions", methods=['POST'])
    def search_questions():
        if request.data:
            current_page = int(request.args.get('page'))
            data = json.loads(request.data.decode('utf-8'))
            if 'searchTerm' in data:
                questions_query = Question.query.filter(
                    Question.question.like(
                        '%' +
                        data['searchTerm'] +
                        '%')).paginate(
                    current_page,
                    QUESTIONS_PER_PAGE,
                    False)
                questions = list(map(Question.format, questions_query.items))
                if len(questions) > 0:
                    return jsonify({
                        "success": True,
                        "questions": questions,
                        "total_questions": questions_query.total
                    })
            abort(404)
        abort(422)

    '''
  @TODO:
  # Done
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''

    @app.route("/categories/<int:category_id>/questions")
    def get_question_by_category(category_id):
        page = int(request.args.get('page'))
        questions_query = Question.query.filter_by(
            category=category_id).paginate(
            page, QUESTIONS_PER_PAGE, False)
        questions = list(map(Question.format, questions_query.items))
        if len(questions) > 0:
            return jsonify({
                "success": True,
                "questions": questions,
                "total_questions": questions_query.total
            })
        abort(404)

    '''
  @TODO:
  # Done
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''

    @app.route("/quizzes", methods=['POST'])
    def get_question_for_quiz():
        data = json.loads(request.data.decode('utf-8'))
        if (('quiz_category' in data
             and 'id' in data['quiz_category'])
                and 'previous_questions' in data):
            questions_query = Question.query.filter_by(
                category=data['quiz_category']['id']
            ).filter(
                Question.id.notin_(data["previous_questions"])
            ).all()
            length_of_available_question = len(questions_query)
            if length_of_available_question > 0:
                return jsonify({
                    "success": True,
                    "question": Question.format(
                        questions_query[random.randrange(
                            0,
                            length_of_available_question
                        )]
                    )
                })
            else:
                return jsonify({
                    "success": True,
                    "question": "no questions found"
                })
        abort(404)

    '''
  @TODO:
  # Done
  Create error handlers for all expected errors
  including 404 and 422.
  '''

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(500)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal server error"
        }), 500

    return app
