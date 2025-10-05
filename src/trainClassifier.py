import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report

# Load training data
data = pd.read_csv("test_data.csv")
X = data["text"]
y = data["label"]

# Split database into testing and training data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Use TfidfVectorizer to turn text into numbers for the  model to train on
vectorizer = TfidfVectorizer(max_features=10)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Run MultinomialNB model on the training data
model = MultinomialNB()
model.fit(X_train_vec, y_train)

# Test the trained model
y_pred = model.predict(X_test_vec)

# Print results
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))