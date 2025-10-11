"""
IC Verification Module (Fixed)
Advanced classifier for determining genuine/fake IC chips using multiple similarity features
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import Levenshtein
from rapidfuzz import fuzz
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract multiple similarity features for IC verification"""
    
    def __init__(self):
        self.manufacturer_aliases = {
            'MICROCHIP': ['MICROCHIP', 'MCHP', 'ATMEL'],
            'STMICROELECTRONICS': ['STMICROELECTRONICS', 'ST', 'STM'],
            'TEXAS_INSTRUMENTS': ['TEXAS_INSTRUMENTS', 'TI', 'TEXAS INSTRUMENTS'],
            'ESPRESSIF': ['ESPRESSIF', 'ESP'],
            'XILINX': ['XILINX', 'XIL'],
            'AMD': ['AMD', 'ADVANCED MICRO DEVICES']
        }
    
    def extract_features(self, recognized_text, candidate_data):
        """Extract comprehensive similarity features"""
        features = {}
        
        # Clean and normalize texts
        recognized_clean = self._normalize_text(recognized_text)
        candidate_marking = self._normalize_text(candidate_data.get('marking_text', ''))
        
        # Basic string similarity
        features.update(self._string_similarity_features(recognized_clean, candidate_marking))
        
        # Character-level features
        features.update(self._character_level_features(recognized_clean, candidate_marking))
        
        # Fuzzy matching features
        features.update(self._fuzzy_features(recognized_clean, candidate_marking))
        
        return features
    
    def _normalize_text(self, text):
        """Normalize text for comparison"""
        if not text:
            return ""
        return re.sub(r'[^A-Z0-9]', '', text.upper()).strip()
    
    def _string_similarity_features(self, text1, text2):
        """Basic string similarity metrics"""
        if not text1 or not text2:
            return {
                'levenshtein_distance': 999,
                'normalized_levenshtein': 0.0,
                'jaro_similarity': 0.0,
                'length_ratio': 0.0
            }
        
        # Levenshtein distance
        lev_dist = Levenshtein.distance(text1, text2)
        max_len = max(len(text1), len(text2))
        norm_lev = 1.0 - (lev_dist / max_len) if max_len > 0 else 0.0
        
        # Jaro similarity
        jaro_sim = Levenshtein.jaro(text1, text2)
        
        # Length ratio
        len_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2)) if max(len(text1), len(text2)) > 0 else 0.0
        
        return {
            'levenshtein_distance': lev_dist,
            'normalized_levenshtein': norm_lev,
            'jaro_similarity': jaro_sim,
            'length_ratio': len_ratio
        }
    
    def _character_level_features(self, text1, text2):
        """Character-level similarity features"""
        if not text1 or not text2:
            return {
                'char_jaccard_similarity': 0.0,
                'digit_overlap': 0.0,
                'letter_overlap': 0.0
            }
        
        # Character sets
        chars1, chars2 = set(text1), set(text2)
        
        # Jaccard similarity
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        jaccard_sim = intersection / union if union > 0 else 0.0
        
        # Digit overlap
        digits1 = set(c for c in text1 if c.isdigit())
        digits2 = set(c for c in text2 if c.isdigit())
        digit_overlap = len(digits1.intersection(digits2)) / max(len(digits1.union(digits2)), 1)
        
        # Letter overlap
        letters1 = set(c for c in text1 if c.isalpha())
        letters2 = set(c for c in text2 if c.isalpha())
        letter_overlap = len(letters1.intersection(letters2)) / max(len(letters1.union(letters2)), 1)
        
        return {
            'char_jaccard_similarity': jaccard_sim,
            'digit_overlap': digit_overlap,
            'letter_overlap': letter_overlap
        }
    
    def _fuzzy_features(self, text1, text2):
        """Fuzzy string matching features"""
        if not text1 or not text2:
            return {
                'fuzzy_ratio': 0.0,
                'fuzzy_partial_ratio': 0.0,
                'fuzzy_token_sort_ratio': 0.0
            }
        
        return {
            'fuzzy_ratio': fuzz.ratio(text1, text2) / 100.0,
            'fuzzy_partial_ratio': fuzz.partial_ratio(text1, text2) / 100.0,
            'fuzzy_token_sort_ratio': fuzz.token_sort_ratio(text1, text2) / 100.0
        }


class ICVerificationClassifier(nn.Module):
    """Deep learning classifier for IC verification"""
    
    def __init__(self, input_dim, hidden_dims=[64, 32, 16], dropout=0.3):
        super(ICVerificationClassifier, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        
        # Build network
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        # Output layer (binary classification)
        layers.append(nn.Linear(prev_dim, 2))
        self.network = nn.Sequential(*layers)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
    
    def forward(self, x):
        logits = self.network(x)
        probabilities = F.softmax(logits, dim=1)
        return logits, probabilities


class ICVerifier:
    """Complete IC Verification System"""
    
    def __init__(self, model_path=None, ic_database_path=None, device='cuda', confidence_threshold=0.6):
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.confidence_threshold = confidence_threshold
        
        # Initialize components
        self.feature_extractor = FeatureExtractor()
        self.ic_database = self._load_ic_database(ic_database_path)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Model state
        self.model = None
        self.is_trained = False
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def _load_ic_database(self, database_path):
        """Load IC database from CSV"""
        if database_path and Path(database_path).exists():
            logger.info(f"Loading IC database from {database_path}")
            return pd.read_csv(database_path)
        else:
            # Try default path
            default_path = Path("../ml-model/ic_dataset.csv")
            if default_path.exists():
                logger.info(f"Loading IC database from {default_path}")
                return pd.read_csv(default_path)
            else:
                # Create minimal database
                logger.warning("Creating minimal IC database")
                return pd.DataFrame({
                    'IC_Model_Number': ['ATmega328P', 'STM32F103C8T6', 'NE555P'],
                    'OEM_Name': ['Microchip', 'STMicroelectronics', 'Texas Instruments'],
                    'Marking_Text': ['ATmega328P', 'STM32F103', 'NE555P'],
                    'Package_Type': ['DIP-28', 'LQFP-48', 'DIP-8']
                })
    
    def prepare_training_data(self, training_data_path):
        """Prepare training data from CSV file"""
        logger.info("Preparing training data...")
        
        if isinstance(training_data_path, str):
            df = pd.read_csv(training_data_path)
        else:
            df = training_data_path
        
        features_list = []
        labels = []
        
        for _, row in df.iterrows():
            candidate_data = {
                'marking_text': row.get('candidate_marking', ''),
                'model': row.get('candidate_model', ''),
                'oem': row.get('candidate_oem', ''),
                'package': row.get('candidate_package', '')
            }
            
            features = self.feature_extractor.extract_features(
                row['recognized_text'], candidate_data
            )
            
            features_list.append(list(features.values()))
            labels.append(row['match_label'])
        
        # Convert to arrays and scale
        X = np.array(features_list)
        y = np.array(labels)
        
        X_scaled = self.scaler.fit_transform(X)
        y_encoded = self.label_encoder.fit_transform(y)
        
        logger.info(f"Prepared {len(X)} samples with {X.shape[1]} features")
        return X_scaled, y_encoded
    
    def train(self, X, y, validation_split=0.2, epochs=100, batch_size=32, learning_rate=0.001):
        """Train the verification classifier"""
        logger.info("Training IC verification classifier...")
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Initialize model
        input_dim = X.shape[1]
        self.model = ICVerificationClassifier(input_dim).to(self.device)
        
        # Setup training
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.LongTensor(y_train).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_val_tensor = torch.LongTensor(y_val).to(self.device)
        
        # Training loop
        best_val_accuracy = 0
        
        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0
            num_batches = len(X_train) // batch_size + (1 if len(X_train) % batch_size > 0 else 0)
            
            for i in range(0, len(X_train), batch_size):
                batch_X = X_train_tensor[i:i+batch_size]
                batch_y = y_train_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                logits, _ = self.model(batch_X)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                val_logits, _ = self.model(X_val_tensor)
                val_predictions = torch.argmax(val_logits, dim=1)
                val_accuracy = (val_predictions == y_val_tensor).float().mean().item()
            
            # Save best model
            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                self.best_model_state = self.model.state_dict().copy()
            
            if epoch % 20 == 0:
                avg_loss = epoch_loss / num_batches
                logger.info(f"Epoch {epoch}: Loss={avg_loss:.4f}, Val Accuracy={val_accuracy:.4f}")
        
        # Load best model
        self.model.load_state_dict(self.best_model_state)
        self.is_trained = True
        
        logger.info(f"Training completed. Best validation accuracy: {best_val_accuracy:.4f}")
        return {'best_val_accuracy': best_val_accuracy}
    
    def train_model(self, verification_pairs, epochs=100, batch_size=32, learning_rate=0.001):
        """Public method to train the verification model"""
        logger.info(f"Training verification model with {len(verification_pairs)} pairs")
        
        # Convert verification pairs to training format
        training_data = []
        for pair in verification_pairs:
            # Find matching candidate from database
            best_match = None
            best_similarity = 0
            
            for _, row in self.ic_database.iterrows():
                similarity = fuzz.ratio(pair['part_number'], row.get('part_number', ''))
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = row
            
            if best_match is not None:
                training_row = {
                    'recognized_text': pair.get('recognized_text', ''),
                    'candidate_marking': best_match.get('part_number', ''),
                    'candidate_model': best_match.get('part_number', ''), 
                    'candidate_oem': best_match.get('manufacturer', ''),
                    'candidate_package': best_match.get('package', ''),
                    'match_label': pair.get('authentic', True)
                }
                training_data.append(training_row)
        
        if not training_data:
            logger.warning("No valid training data generated from verification pairs")
            return {'best_val_accuracy': 0.0}
        
        logger.info(f"Generated {len(training_data)} training samples")
        
        # Prepare and train
        X, y = self.prepare_training_data(pd.DataFrame(training_data))
        return self.train(X, y, epochs=epochs, batch_size=batch_size, learning_rate=learning_rate)
    
    def verify_ic(self, recognized_text, ocr_confidence=1.0, top_k=3):
        """Verify IC authenticity against database"""
        
        if not self.is_trained:
            logger.warning("Model not trained, using rule-based verification")
            return self._rule_based_verification(recognized_text)
        
        # Find candidate ICs
        candidates = self._find_candidates(recognized_text, top_k)
        
        if not candidates:
            return {
                'status': 'FRAUD/UNKNOWN',
                'confidence': 0.0,
                'message': 'No matching IC found in database',
                'candidates': []
            }
        
        # Verify each candidate
        verification_results = []
        
        for candidate in candidates:
            features = self.feature_extractor.extract_features(recognized_text, candidate)
            feature_vector = np.array(list(features.values())).reshape(1, -1)
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict
            self.model.eval()
            with torch.no_grad():
                feature_tensor = torch.FloatTensor(feature_vector_scaled).to(self.device)
                logits, probabilities = self.model(feature_tensor)
                genuine_prob = probabilities[0, 1].item()
                is_genuine = genuine_prob > self.confidence_threshold
            
            verification_results.append({
                'candidate': candidate,
                'genuine_probability': genuine_prob,
                'is_genuine': is_genuine
            })
        
        # Select best result
        verification_results.sort(key=lambda x: x['genuine_probability'], reverse=True)
        best_result = verification_results[0]
        
        # Combine confidences
        combined_confidence = (best_result['genuine_probability'] + ocr_confidence) / 2
        
        # Final decision
        if best_result['is_genuine'] and combined_confidence > self.confidence_threshold:
            status = 'AUTHENTIC'
            message = f"IC verified as genuine with {combined_confidence:.1%} confidence"
        else:
            status = 'FRAUD/UNKNOWN'
            message = f"IC could not be verified as genuine (confidence: {combined_confidence:.1%})"
        
        return {
            'status': status,
            'confidence': combined_confidence,
            'message': message,
            'matched_ic': best_result['candidate'] if best_result['is_genuine'] else None,
            'possible_matches': [r['candidate'] for r in verification_results[:3]]
        }
    
    def _find_candidates(self, recognized_text, top_k=3):
        """Find candidate ICs from database using fuzzy matching"""
        candidates = []
        
        for _, row in self.ic_database.iterrows():
            candidate = {
                'marking_text': row.get('Marking_Text', ''),
                'model': row.get('IC_Model_Number', ''),
                'oem': row.get('OEM_Name', ''),
                'package': row.get('Package_Type', ''),
                'datasheet_url': row.get('Datasheet_URL', ''),
                'release_date': row.get('Release_Date', '')
            }
            
            # Quick similarity check
            similarity = fuzz.ratio(recognized_text.upper(), 
                                  candidate['marking_text'].upper()) / 100.0
            
            if similarity > 0.2:  # Basic threshold
                candidate['initial_similarity'] = similarity
                candidates.append(candidate)
        
        # Sort and return top candidates
        candidates.sort(key=lambda x: x['initial_similarity'], reverse=True)
        return candidates[:top_k]
    
    def _rule_based_verification(self, recognized_text):
        """Fallback rule-based verification when model is not trained"""
        best_match = None
        best_similarity = 0.0
        
        for _, row in self.ic_database.iterrows():
            marking_text = row.get('Marking_Text', '')
            similarity = fuzz.ratio(recognized_text.upper(), marking_text.upper()) / 100.0
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'model': row.get('IC_Model_Number', ''),
                    'oem': row.get('OEM_Name', ''),
                    'marking_text': marking_text,
                    'package': row.get('Package_Type', ''),
                    'datasheet_url': row.get('Datasheet_URL', '')
                }
        
        # Decision based on similarity
        if best_similarity > self.confidence_threshold:
            status = 'AUTHENTIC'
            message = f"IC matched with {best_similarity:.1%} similarity (rule-based)"
        else:
            status = 'FRAUD/UNKNOWN'
            message = f"Low similarity match: {best_similarity:.1%} (rule-based)"
        
        return {
            'status': status,
            'confidence': best_similarity,
            'message': message,
            'matched_ic': best_match if status == 'AUTHENTIC' else None,
            'method': 'rule_based'
        }
    
    def save_model(self, save_path):
        """Save trained model and preprocessing objects"""
        if not self.is_trained:
            logger.warning("Model not trained, nothing to save")
            return
        
        save_data = {
            'model_state_dict': self.model.state_dict(),
            'model_config': {
                'input_dim': self.model.input_dim,
                'hidden_dims': self.model.hidden_dims
            },
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'confidence_threshold': self.confidence_threshold
        }
        
        torch.save(save_data, save_path)
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, model_path):
        """Load trained model and preprocessing objects"""
        logger.info(f"Loading model from {model_path}")
        
        # Add safe globals for sklearn objects
        import torch.serialization
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        
        with torch.serialization.safe_globals([StandardScaler, LabelEncoder]):
            if self.device == 'cpu':
                save_data = torch.load(model_path, map_location='cpu', weights_only=False)
            else:
                save_data = torch.load(model_path, weights_only=False)
        
        # Load model
        model_config = save_data['model_config']
        self.model = ICVerificationClassifier(
            input_dim=model_config['input_dim'],
            hidden_dims=model_config['hidden_dims']
        ).to(self.device)
        
        self.model.load_state_dict(save_data['model_state_dict'])
        self.model.eval()
        
        # Load preprocessing objects
        self.scaler = save_data['scaler']
        self.label_encoder = save_data['label_encoder']
        self.confidence_threshold = save_data.get('confidence_threshold', 0.6)
        
        self.is_trained = True
        logger.info("Model loaded successfully")


if __name__ == "__main__":
    # Test IC verifier
    verifier = ICVerifier()
    
    # Test verification
    result = verifier.verify_ic("ATmega328P")
    
    print("Verification Result:")
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Message: {result['message']}")
    
    if result.get('matched_ic'):
        print(f"Matched IC: {result['matched_ic']['model']}")
    
    print("IC Verifier test completed")