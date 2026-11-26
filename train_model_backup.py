import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
data = pd.read_csv("courses.csv")

# Combine course features
data["combined_features"] = (
    data["interests"].fillna("") + " " +
    data["skills"].fillna("") + " " +
    data["subjects"].fillna("") + " " +
    data["department"].fillna("")
)

# Convert text into numerical vectors
vectorizer = TfidfVectorizer()
feature_matrix = vectorizer.fit_transform(data["combined_features"])

# Calculate similarity
similarity_matrix = cosine_similarity(feature_matrix)

print("ML Recommendation Model Trained Successfully!")
print("Total Courses:", len(data))
print("Feature Matrix:", feature_matrix.shape)
print("Similarity Matrix:", similarity_matrix.shape)
def recommend_courses(student_interests, student_skills, top_n=5):

    student_profile = student_interests + " " + student_skills

    student_vector = vectorizer.transform([student_profile])

    scores = cosine_similarity(student_vector, feature_matrix)[0]

    top_indices = scores.argsort()[::-1][:top_n]

    recommendations = data.iloc[top_indices][
        ["programme", "level", "department", "campus"]
    ].copy()

    recommendations["match_score"] = (
        scores[top_indices] * 100
    ).round(2)

    return recommendations


# Test recommendation
results = recommend_courses(
    "Artificial Intelligence, Machine Learning, Data Science",
    "Python, Statistics, Data Analysis"
)

print("\nRecommended Courses:")
print(results.to_string(index=False))