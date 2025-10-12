import random
import string
import os
import csv
from typing import List, Tuple, Dict
import wonderwords
import faker

from ..interfaces import (
    LanguageDataGenerator, DatasetGeneratorInterface, LanguageConfig
)


class DataGenerator(LanguageDataGenerator):
    """English language data generator implementation"""
    
    def __init__(self):
        super().__init__("en", "en_US")
        self.rword = wonderwords.RandomWord()
        self.rsent = wonderwords.RandomSentence()
        self.fake = faker.Faker('en_US')
    
    def generate_name(self) -> str:
        return self.fake.name()
    
    def generate_sentence(self) -> str:
        return self.rsent.sentence()
    
    def generate_paragraph(self) -> str:
        return self.rsent.sentence() + " " + self.rsent.sentence() + " " + self.rsent.sentence()
    
    def generate_word(self) -> str:
        return self.rword.word()
    
    def generate_phone(self) -> str:
        return self.fake.phone_number()
    
    def generate_address(self) -> str:
        return self.fake.address()
    
    def generate_date(self) -> str:
        return self.fake.date()
    
    def get_ocr_confusion_chars(self) -> Dict[str, List[str]]:
        return {
            's1': ['8', 'S', '5', 's', 'B'],
            's2': ['0', 'O', 'o', 'Q'],
            's3': ['i', 'I', 'l', '/']
        }


class DatasetGenerator(DatasetGeneratorInterface):
    """English dataset generator implementation"""
    
    def __init__(self, language_generator: DataGenerator = DataGenerator()):
        super().__init__(language_generator)
    
    def get_sentence_fragment(self, template: str, min_length: int = 5, max_length: int = 20) -> str:
        tokens = template.split(" ")
        if len(tokens) < min_length:
            return template
        
        fragment_range = random.randint(min_length, min(max_length, len(tokens)))
        start_index = random.randint(0, len(tokens) - fragment_range)
        fragment = tokens[start_index:start_index + fragment_range]
        return " ".join(fragment)
    
    def generate_dataset(self, templates: Dict[str, str], num_samples: int, 
                        ocr_error_rate: float, output_file: str) -> None:
        if os.path.exists(output_file):
            os.remove(output_file)
        
        all_template_paths = list(templates.values())
        data = []
        
        for label, template_path in templates.items():
            template_data = self._generate_template_data(
                template_path, label, num_samples, ocr_error_rate, all_template_paths
            )
            data.extend(template_data)
        
        # Save to CSV
        file_exists = os.path.exists(output_file)
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['text', 'label'])
            writer.writerows(data)
    
    def _generate_template_data(self, template_path: str, doc_type: str, 
                              num_samples: int, ocr_error_rate: float, 
                              all_templates: List[str]) -> List[List[str]]:
        data = []
        
        with open(template_path, 'r', encoding='utf-8') as template_file:
            line = template_file.readline()
            segments = line.split(" ")
        
        for i in range(num_samples):
            gen_copy = ""
            
            # 10% chance to include fragment from other template
            if random.random() < 0.1:
                other_template_path = random.choice(all_templates)
                if other_template_path != template_path:
                    with open(other_template_path, 'r', encoding='utf-8') as other_file:
                        other_text = other_file.readline()
                        other_fragment = self.get_sentence_fragment(other_text)
                        gen_copy += other_fragment
            
            # Process template segments
            for segment in segments:
                if segment == "{ID}":
                    gen_copy += str(random.randrange(0, 9999))
                elif segment == "{Name}":
                    gen_copy += self.language_generator.generate_name()
                elif segment == "{Sentence}":
                    gen_copy += self.language_generator.generate_sentence()
                elif segment == "{Paragraph}":
                    gen_copy += self.language_generator.generate_paragraph()
                elif segment == "{Word}":
                    gen_copy += self.language_generator.generate_word()
                elif segment == "{Phone}":
                    gen_copy += self.language_generator.generate_phone()
                elif segment == "{Address}":
                    gen_copy += self.language_generator.generate_address()
                elif segment == "{Date}":
                    gen_copy += self.language_generator.generate_date()
                else:
                    gen_copy += segment
                gen_copy += " "
            
            # Apply OCR errors
            final_string = self._apply_ocr_errors(gen_copy, ocr_error_rate)
            data.append([final_string, doc_type])
        
        return data
    
    def _apply_ocr_errors(self, text: str, error_rate: float) -> str:
        confusion_chars = self.language_generator.get_ocr_confusion_chars()
        final_string = ""
        
        for char in text:
            if random.random() < error_rate:
                if char in confusion_chars['s1']:
                    final_string += random.choice(confusion_chars['s1'])
                elif char in confusion_chars['s2']:
                    final_string += random.choice(confusion_chars['s2'])
                elif char in confusion_chars['s3']:
                    final_string += random.choice(confusion_chars['s3'])
                else:
                    final_string += random.choice(string.ascii_letters)
            else:
                final_string += char
        
        return final_string
    
    def generate_template_data(self, template_path: str, doc_type: str, 
                             num_samples: int, ocr_error_rate: float, 
                             all_templates: List[str]) -> List[List[str]]:
        data = []
        
        with open(template_path, 'r', encoding='utf-8') as template_file:
            line = template_file.readline()
            segments = line.split(" ")
        
        for i in range(num_samples):
            gen_copy = ""
            
            # 10% chance to include fragment from other template
            if random.random() < 0.1:
                other_template_path = random.choice(all_templates)
                if other_template_path != template_path:
                    with open(other_template_path, 'r', encoding='utf-8') as other_file:
                        other_text = other_file.readline()
                        other_fragment = self.get_sentence_fragment(other_text)
                        gen_copy += other_fragment
            
            # Process template segments
            for segment in segments:
                if segment == "{ID}":
                    gen_copy += str(random.randrange(0, 9999))
                elif segment == "{Name}":
                    gen_copy += self.language_generator.generate_name()
                elif segment == "{Sentence}":
                    gen_copy += self.language_generator.generate_sentence()
                elif segment == "{Paragraph}":
                    gen_copy += self.language_generator.generate_paragraph()
                elif segment == "{Word}":
                    gen_copy += self.language_generator.generate_word()
                elif segment == "{Phone}":
                    gen_copy += self.language_generator.generate_phone()
                elif segment == "{Address}":
                    gen_copy += self.language_generator.generate_address()
                elif segment == "{Date}":
                    gen_copy += self.language_generator.generate_date()
                else:
                    gen_copy += segment
                gen_copy += " "
            
            # Apply OCR errors
            final_string = self._apply_ocr_errors(gen_copy, ocr_error_rate)
            data.append([final_string, doc_type])
        
        return data
    
    def _apply_ocr_errors(self, text: str, error_rate: float) -> str:
        confusion_chars = self.language_generator.get_ocr_confusion_chars()
        final_string = ""
        
        for char in text:
            if random.random() < error_rate:
                if char in confusion_chars['s1']:
                    final_string += random.choice(confusion_chars['s1'])
                elif char in confusion_chars['s2']:
                    final_string += random.choice(confusion_chars['s2'])
                elif char in confusion_chars['s3']:
                    final_string += random.choice(confusion_chars['s3'])
                else:
                    final_string += random.choice(string.ascii_letters)
            else:
                final_string += char
        
        return final_string


