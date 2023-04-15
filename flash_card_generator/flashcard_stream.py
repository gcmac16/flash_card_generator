import tiktoken
import openai
from dotenv import load_dotenv
from models.flashcard import FlashCard
import os


PROMPT = """You are a tutor that helps students learn concepts by making
flash cards. I will send you text to make flashcards for. you will synthesize
the information and return a single flash card. A flash card text composed of 
two keys "front" and "back". The front has a concept/question on it and
the back has a definition/answer. The next message has the text; please create one
json flash card to start with. An example of the output is:
Front: What 
Back: 
"""

FOLLOWUP = """Thank you! Now return another flashcard object for the 
next most important concept from the same text. Please don't repeat one
of the previous flashcards.
"""
CHUNK_SIZE = 500

# Load in environment variables from .env-secrets file
load_dotenv(".env-secrets")
openai.api_key = os.getenv("OPEN_API_KEY")


class FlashCardStream(object):

    def __init__(
            self, 
            text: str,
            model: str, 
            user_id: int,
            print_text: bool = True,
            cards_per_chunk: int = 2,
            chunk_size: int = 500
    ):
        self.text = text
        self.model = model
        self.user_id = user_id
        self.print_text = print_text
        self.cards_per_chunk = cards_per_chunk
        self.chunk_size = chunk_size
        self.split_text = None
        
        self._split_text()

    def get_flashcards(self):
        all_flashcards = []
        for text_segment in self.split_text:
            all_flashcards.extend(
                self._build_flashcards_for_segment(text_segment))
            
        return all_flashcards

    def _split_text(self):
        encoder = tiktoken.encoding_for_model(self.model)
        encoded_text = encoder.encode(self.text)
        output = []
    
        while len(encoded_text)  > 0:
            chunk = encoded_text[:self.chunk_size]
            encoded_text = encoded_text[self.chunk_size:]
            output.append(encoder.decode(chunk))
            
        self.split_text = output

    def _extract_text_from_response(self, response: str):
        response_text = response['choices'][0]['message']['content']
    
        if self.print_text:
            print(f"Model Response: ")
            print(response_text)
        
        return response_text

    def _build_flashcards_for_segment(
            self,
            text_segment: str, 
            n_cards: int = 3, 
    ) -> list[FlashCard]:
        messages = [
            {"role": 
                "system", 
                "content": """you are a helpful tutor that makes excellent flash
                cards for studying. you don't repeat yourself"""
            },
            {"role": "user", "content": PROMPT},
            {"role": "user", "content": text_segment}
        ]
        
        all_flashcards = []
        new_flashcards = []
        for i in range(n_cards):
            print(f"Running message {i+1}")
            for card in new_flashcards:
                content = (
                    f"Don't repeat this flashcard you just"
                    f"added {card.get_prompt_text()}"
                )
                messages.append({
                    "role": "assistant",
                    "content": content
                })
            
            messages.append({
                "role": "user", 
                "content": FOLLOWUP
            })
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
            )
            
            # don't want to repeat this every time
            messages.pop()
            
            response_text = self._extract_text_from_response(response)
            flashcards = self._extract_data_from_model_response(response_text)
            all_flashcards.extend(flashcards)
            new_flashcards = flashcards[:]
    
        return all_flashcards
    
    def _extract_data_from_model_response(self, input: str) -> list[FlashCard]:
        words = input.split()
    
        # Find indices where "front:" and "back:" occur
        front_indices = [i for i, word in enumerate(words) if word.lower() == "front:"]
        back_indices = [i for i, word in enumerate(words) if word.lower() == "back:"]
    
        # Iterate through each pair of front/back indices
        output = []
        for front_idx, back_idx in zip(front_indices, back_indices):
            front = ' '.join(words[front_idx+1:back_idx]).strip()
            back = ' '.join(words[back_idx+1:]).strip()
            output.append(FlashCard(front=front, back=back, user_id=self.user_id))
    
        return output