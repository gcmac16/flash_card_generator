from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.flashcard import (
    FlashCard,
)
from models.user import (
    Base, 
    User,
)
from flashcard_stream import FlashCardStream
from dotenv import load_dotenv
import openai
import os

app = Flask(__name__)

# Database setup
# Load in environment variables from .env-secrets file
load_dotenv(".env-secrets")
openai.api_key = os.getenv("OPEN_API_KEY")

# Get environment variable values
DB_CONN = os.getenv("DB_CONN")
engine = create_engine(DB_CONN)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@app.route('/')
def landing_page():
    return render_template('landing_page.html')
    

def authenticate_user(email, password):
    session = Session()
    user = session.query(User).filter_by(email=email).first()
    if user and user.check_password(password):
        return user
    return None


@app.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"message": "Hello, world!"}), 200

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Check if user exists
    session = Session()
    existing_user = session.query(User).filter_by(email=email).first()

    if existing_user is not None:
        return jsonify({'error': 'User already exists'}), 400

    # Create new user
    user = User(email=email)
    user.set_password(password)
    session.add(user)
    session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@app.route('/create_flashcards', methods=['POST'])
def create_flashcards():
    data = request.get_json()
    # email = data.get('email')
    # password = data.get('password')
    text = data.get('text')

    # user = authenticate_user(email, password)
    # if not user:
    #     return jsonify({"error": "Invalid email or password"}), 401

    # Call the function to generate flashcards from the text
    flashcard_stream = FlashCardStream(text, 'gpt-3.5-turbo', 1)
    flashcards = flashcard_stream.get_flashcards()

    # session = Session()
    # for fc_data in flashcards_data:
    #     flashcard = FlashCard(front=fc_data['front'], back=fc_data['back'], user_id=user.id)
    #     session.add(flashcard)

    # session.commit()
    # session.close()

    return jsonify({
        "message": "Flashcards created successfully", 
        "flashcards": [
            flashcard.to_json() 
            for flashcard in flashcards
        ]
    })


if __name__ == '__main__':
    app.run(debug=True)