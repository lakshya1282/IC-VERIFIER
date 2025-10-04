import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import json
from datetime import datetime

class ICVerificationModel:
    def __init__(self, csv_path='ic_dataset.csv'):
        """Initialize the IC Verification Model"""
        self.csv_path = csv_path
        self.df = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.load_data()
        
    def load_data(self):
        """Load IC data from CSV"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"Loaded {len(self.df)} IC records from dataset")
            print(f"Columns: {list(self.df.columns)}")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def preprocess_text(self, text):
        """Preprocess marking text for better matching"""
        if pd.isna(text):
            return ""
        return str(text).upper().strip()
    
    def train(self):
        """Train the model using TF-IDF vectorization"""
        print("\n=== Training IC Verification Model ===")
        
        # Preprocess marking text
        self.df['processed_marking'] = self.df['Marking_Text'].apply(self.preprocess_text)
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 4),
            min_df=1,
            lowercase=True
        )
        
        # Fit and transform the marking texts
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['processed_marking'])
        
        print(f"Model trained with {self.tfidf_matrix.shape[0]} samples")
        print(f"Feature vocabulary size: {len(self.vectorizer.vocabulary_)}")
        
    def verify_ic(self, scanned_text, threshold=0.6):
        """
        Verify IC marking against database
        Returns verification result with confidence score
        """
        # Preprocess scanned text
        processed_scan = self.preprocess_text(scanned_text)
        
        # Transform scanned text to TF-IDF vector
        scan_vector = self.vectorizer.transform([processed_scan])
        
        # Calculate similarity scores
        similarities = cosine_similarity(scan_vector, self.tfidf_matrix)[0]
        
        # Get best match
        best_match_idx = np.argmax(similarities)
        confidence = float(similarities[best_match_idx])
        
        result = {
            'scanned_text': scanned_text,
            'is_valid': confidence >= threshold,
            'confidence': confidence,
            'threshold': threshold
        }
        
        if confidence >= threshold:
            match = self.df.iloc[best_match_idx]
            result['matched_ic'] = {
                'ic_model': match['IC_Model_Number'],
                'oem_name': match['OEM_Name'],
                'package_type': match['Package_Type'],
                'marking_text': match['Marking_Text'],
                'datasheet_url': match['Source_URL'],
                'release_date': match['Release_Date']
            }
            result['status'] = 'AUTHENTIC'
            result['message'] = f'IC verified as authentic {match["OEM_Name"]} {match["IC_Model_Number"]}'
        else:
            result['matched_ic'] = None
            result['status'] = 'FRAUD/UNKNOWN'
            result['message'] = 'IC marking not found in OEM database. Possible fraud or unknown IC.'
            
            # Provide top 3 closest matches for reference
            top_3_indices = np.argsort(similarities)[-3:][::-1]
            result['possible_matches'] = []
            for idx in top_3_indices:
                if similarities[idx] > 0.3:
                    match = self.df.iloc[idx]
                    result['possible_matches'].append({
                        'ic_model': match['IC_Model_Number'],
                        'oem_name': match['OEM_Name'],
                        'marking_text': match['Marking_Text'],
                        'similarity': float(similarities[idx])
                    })
        
        return result
    
    def save_model(self, model_path='ic_model.pkl', metadata_path='ic_metadata.json'):
        """Save trained model and metadata"""
        model_data = {
            'vectorizer': self.vectorizer,
            'tfidf_matrix': self.tfidf_matrix,
            'dataframe': self.df
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        metadata = {
            'training_date': datetime.now().isoformat(),
            'num_samples': len(self.df),
            'ic_manufacturers': list(self.df['OEM_Name'].unique()),
            'total_ic_models': len(self.df),
            'model_version': '1.0'
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nModel saved to {model_path}")
        print(f"Metadata saved to {metadata_path}")
    
    @staticmethod
    def load_model(model_path='ic_model.pkl'):
        """Load a pre-trained model"""
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        model = ICVerificationModel.__new__(ICVerificationModel)
        model.vectorizer = model_data['vectorizer']
        model.tfidf_matrix = model_data['tfidf_matrix']
        model.df = model_data['dataframe']
        
        print(f"Model loaded from {model_path}")
        return model


def main():
    """Main training script"""
    print("IC Verification System - Model Training")
    print("=" * 50)
    
    # Initialize and train model
    model = ICVerificationModel('ic_dataset.csv')
    model.train()
    
    # Save model
    model.save_model()
    
    # Test the model with sample verifications
    print("\n=== Testing Model ===")
    
    test_cases = [
        "ATMEL 328P U",          # Should match ATmega328P
        "STM32F103C8T6",         # Should match STM32F103C8T6
        "NE555P",                # Should match NE555P
        "FAKE12345XYZ",          # Should not match (fraud)
        "LM358N TI"              # Should match LM358N
    ]
    
    for test_text in test_cases:
        print(f"\nTesting: '{test_text}'")
        result = model.verify_ic(test_text)
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence']:.2%}")
        if result['matched_ic']:
            print(f"Matched: {result['matched_ic']['oem_name']} - {result['matched_ic']['ic_model']}")
        print(f"Message: {result['message']}")
    
    print("\n" + "=" * 50)
    print("Training complete! Model ready for deployment.")
    print("\nTo use the model in your application:")
    print("  from train_model import ICVerificationModel")
    print("  model = ICVerificationModel.load_model('ic_model.pkl')")
    print("  result = model.verify_ic('scanned_text')")


if __name__ == "__main__":
    main()
