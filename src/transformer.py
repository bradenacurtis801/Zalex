from sentence_transformers import SentenceTransformer

class Transformer:

    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def encode(self,sentences):
        return self.model.encode(sentences)

    def train(self):
        pass

    def load(self,dir):
        pass

    def store(self,dir):
        pass