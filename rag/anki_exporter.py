import os
import random
import genanki

class AnkiExporter:
    def __init__(self):
        # Anki requires mathematically unique IDs for Models and Decks
        self.model_id = random.randrange(1 << 30, 1 << 31)
        
        # Define the HTML/CSS template for how the cards will look inside the real Anki app
        self.model = genanki.Model(
            self.model_id,
            'Auto-Anki AI Model',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
            ],
            templates=[
                {
                    'name': 'Standard Card',
                    'qfmt': '<div style="font-family: sans-serif; font-size: 22px; text-align: center; padding: 20px;">{{Question}}</div>',
                    'afmt': '{{FrontSide}}<hr id="answer"><div style="font-family: sans-serif; font-size: 18px; color: #10b981; text-align: center; padding: 20px;">{{Answer}}</div>',
                },
            ])

    def export_to_apkg(self, deck_name: str, cards: list, output_dir: str = "exports"):
        # Create exports folder if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        deck_id = random.randrange(1 << 30, 1 << 31)
        deck = genanki.Deck(deck_id, deck_name)

        # Loop through our AI generated JSON cards and convert them to Anki Notes
        for card in cards:
            question = str(card.get("question", "")).strip()
            answer = str(card.get("answer", "")).strip()
            
            if question and answer:
                note = genanki.Note(
                    model=self.model,
                    fields=[question, answer]
                )
                deck.add_note(note)

        # Clean the filename (remove weird characters)
        safe_name = deck_name.replace(" ", "_").replace("/", "-").replace(":", "")
        output_path = os.path.join(output_dir, f"{safe_name}.apkg")
        
        # Package and export!
        genanki.Package(deck).write_to_file(output_path)
        return output_path