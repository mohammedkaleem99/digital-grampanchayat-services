import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import joblib
import os

# Create dummy data for training
data = {
    'message': [
        "Water pipe is broken and leaking everywhere",
        "Need a new water connection",
        "No electricity for 3 days",
        "Street light is flickering",
        "Gram panchayat office is closed during working hours",
        "Road is completely damaged and dangerous",
        "Pothole in front of my house",
        "Requesting income certificate",
        "Emergency, huge fire near the transformer",
        "Garbage not collected today",
        "Dead animal on the road creating bad smell",
        "Need to submit birth certificate application"
    ],
    'urgency_level': [
        'urgent',
        'normal',
        'urgent',
        'normal',
        'urgent',
        'urgent',
        'normal',
        'normal',
        'urgent',
        'normal',
        'urgent',
        'normal'
    ]
}

def train_and_save_model():
    print("Training ML model for complaint classification...")
    df = pd.DataFrame(data)

    # We use a pipeline that vectorizes the text and then applies Logistic Regression
    model = make_pipeline(
        TfidfVectorizer(stop_words='english'),
        LogisticRegression(random_state=42)
    )

    # Train the model
    model.fit(df['message'], df['urgency_level'])

    # Ensure ml directory exists
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Save the pipeline to a joblib file
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'complaint_model.joblib')
    joblib.dump(model, model_path)
    
    print(f"Model successfully saved at {model_path}!")

    # Test the model with some unseen data
    test_complaints = [
        "There is a huge accident on the main road",
        "Please issue my death certificate",
        "No drinking water supply since morning"
    ]
    predictions = model.predict(test_complaints)
    print("\nTest Predictions:")
    for text, pred in zip(test_complaints, predictions):
        print(f"'{text}' -> {pred}")

if __name__ == "__main__":
    train_and_save_model()
