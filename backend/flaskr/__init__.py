import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE     # eg start page = 1. 1 - 1 = 0, 0 * 10 = 0.
  end = start + QUESTIONS_PER_PAGE            # end = 0 + 10 if page 1.

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]    # take questions from position 0 - 10

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={'/': {'origins': '*'}})
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers','Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods','GET,PUT,DELETE,POST,OPTIONS') # allow selected methods
    return response
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()               # get all categories
    categories_dict = {}                          
    for category in categories:                     
      categories_dict[category.id] = category.type

    if (len(categories_dict) == 0):                 # if no categories throw error
      abort(404)
    
    return jsonify({
      'success': True,
      'categories': categories_dict                 # return categories
    })


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():

    selection = Question.query.all()                          # select all questions
    total_questions = len(selection)                          # total number of Qs from length
    current_questions = paginate_questions(request,selection) 

    categories = Category.query.all()                         # get all categories
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type
      
    if (len(current_questions) == 0):                         # throw error if no questions
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,                         # return questions, total num, and categories
      'total_questions': total_questions,
      'categories': categories_dict
    })
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  
  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_question(id):
  
    try:

      question = Question.query.filter_by(id=id).one_or_none()    # find the question by ID, Either returns the question or NONE if not found

      if question is None:
        abort(404)                                                # question by id not found throw error

      question.delete()                                           # if found delete

      return jsonify({
        'success': True,
        'deleted': id
      })
    
    except:
      abort(422)
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  

  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('questions', methods=['POST'])
  def post_question():

    body = request.get_json()

    if (body.get('searchTerm')):                # if search box filled
      search_term = body.get('searchTerm')      # get search term

      selection = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all() # return all questions where there is a partial match on the search term

      if (len(selection) == 0):                         # if nothing found throw error
        abort(404)

      paginated = paginate_questions(request,selection) # paginate the return questions

      return jsonify({
        'success': True,
        'questions': paginated,
        'total_questions': len(Question.query.all())
      })
    else:
      new_question = body.get('question')             # add in a new question
      new_answer = body.get('answer')
      new_difficulty = body.get('difficulty')
      new_category = body.get('category')
# if 1 or more form fields not filled out then throw the error below
      if ((new_question is None) or (new_answer is None) or (new_difficulty is None) or (new_category is None)):
        abort(422)
      
      try:

        question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
        question.insert()                                           # add the new question

        selection = Question.query.order_by(Question.id).all()      # add new question to current questions return by ID
        current_questions = paginate_questions(request, selection)  # paginate the questions including new one

        return jsonify({
          'success': True,
          'created': question.id,
          'question_created': question.question,
          'questions': current_questions,
          'total_questions': len(Question.query.all())
        })

      except:
        
        abort(422)


  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions')
  def get_questions_by_category(id):

    category = Category.query.filter_by(id=id).one_or_none()        # check you have a record for that category
    if(category is None):
      abort(400)

    selection = Question.query.filter_by(category=category.id).all()  # load all questions where the category ID matches what was entered

    paginated = paginate_questions(request, selection)              # paginate the current list

    return jsonify({
      'success': True,
      'questions': paginated,
      'total_questions': len(Question.query.all()),
      'current_category': category.type
    })

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_random_quiz_questions():

    body = request.get_json()

    previous = body.get('previous_quesitons')       # get previous questions

    category = body.get('quiz_category')            # get category

    if ((category is None) or (previous is None)):  # throw error is neither of the above
      abort(400)

    if(category['id'] == 0):
      questions = Question.query.all()              # get all questions
    else:
      questions = Question.query.filter_by(category=category['id']).all() # or get all questions for that category

    total = len(questions)                          # num of all questions found

    def get_random_questions():
      return questions[random.randrange(0, len(questions), 1)]  # choose a random question between 0 and total number of questions

    def used_questions(question):
      used = False                        # has question been used. set to false
      for q in previous:                  # check question against previous questions
        if(q == question.id):             # if IDs match
          used = True                     # then it has been used

        return used

    question = get_random_questions()

    while (used_questions(question)):
      question = get_random_questions()

      if (len(previous) == total):
        return jsonify({
          'success': True
        })

    return jsonify({
      'success': True,
      'question': question.format()
    })
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
# the below is error messages with details 
  @app.errorhandler(400)
  def bad_request(erro):
    return jsonify({
      'success': False,
      'error': 400,
      'error message': 'bad request'
    }), 400
  
  @app.errorhandler(404)
  def not_found(erro):
    return jsonify({
      'success': False,
      'error': 404,
      'error message': 'resource not found'
    }), 404

  @app.errorhandler(422)
  def unprocessable(erro):
    return jsonify({
      'success': False,
      'error': 422,
      'error message': 'unprocessable'
    }), 422

  return app

    