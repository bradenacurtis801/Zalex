import faiss
import numpy

class Embeddings:
    originalSentences = []

    def __init__(self,transformer):#creates a fiass index with IVFPQ structure
        self.transformer = transformer
        self.embeddings = faiss.IndexIVFPQ(faiss.IndexFlatL2(384),384,10,16,8)

    def add(self, sentences):
        self.originalSentences += sentences
        newembeddings = self.transformer.encode(sentences)
        self.embeddings.add(newembeddings)

    def remove(self,indexes):#removes the index from the search list but retains the same id structure
        self.embeddings.remove_ids(numpy.array(indexes,dtype=numpy.int64))

    def search(self,sentence,depth):#returns a list of the top results
        embeddedSentence = self.transformer.encode([sentence])
        distances, indecies = self.embeddings.search(embeddedSentence,depth)
        results = []
        for loc in indecies[0]:
            results.append(self.originalSentences[loc.item()])
        return results

    def train(self,sentences):#trains the model structure for more efficient searching
        newembeddings = self.transformer.encode(sentences)
        self.embeddings.train(newembeddings)

    def storeEmbeddings(self,path):
        faiss.write_index(self.embeddings,path)

    def loadEmbeddings(self,path):
        self.embeddings = faiss.read_index(path)