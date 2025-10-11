"""
CRNN Text Recognition Module
Convolutional Recurrent Neural Network for IC marking recognition
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
import cv2
import numpy as np
from collections import OrderedDict
import string
import math


class BidirectionalLSTM(nn.Module):
    """Bidirectional LSTM layer for sequence modeling"""
    
    def __init__(self, nIn, nHidden, nOut):
        super(BidirectionalLSTM, self).__init__()
        
        self.rnn = nn.LSTM(nIn, nHidden, bidirectional=True, batch_first=True)
        self.embedding = nn.Linear(nHidden * 2, nOut)

    def forward(self, input):
        self.rnn.flatten_parameters()
        recurrent, _ = self.rnn(input)
        b, T, h = recurrent.size()  # batch_first=True
        t_rec = recurrent.view(b * T, h)

        output = self.embedding(t_rec)  # [b * T, nOut]
        output = output.view(b, T, -1)

        return output


class ResNet_FeatureExtractor(nn.Module):
    """ResNet-based feature extraction backbone"""
    
    def __init__(self, input_channel, output_channel=512):
        super(ResNet_FeatureExtractor, self).__init__()
        self.output_channel = output_channel
        
        # Initial convolution
        self.ConvNet = nn.Sequential(
            nn.Conv2d(input_channel, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(True),
            nn.MaxPool2d(2, 2),  # 32x16x64
            
            nn.Conv2d(32, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.MaxPool2d(2, 2),  # 64x8x32
            
            nn.Conv2d(64, 128, 3, 1, 1), nn.BatchNorm2d(128), nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),  # 128x4x32
            
            nn.Conv2d(128, 128, 3, 1, 1), nn.BatchNorm2d(128), nn.ReLU(True),
            
            nn.Conv2d(128, 256, 3, 1, 1), nn.BatchNorm2d(256), nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),  # 256x2x32
            
            nn.Conv2d(256, 256, 3, 1, 1), nn.BatchNorm2d(256), nn.ReLU(True),
            
            nn.Conv2d(256, output_channel, 2, 1, 0), nn.BatchNorm2d(output_channel), nn.ReLU(True),  # 512x1x(width/8)
            nn.AdaptiveAvgPool2d((1, None))  # Ensure height is 1
        )

    def forward(self, input):
        return self.ConvNet(input)


class AttentionCell(nn.Module):
    """Attention mechanism for CRNN"""
    
    def __init__(self, input_size, hidden_size, num_classes):
        super(AttentionCell, self).__init__()
        self.i2h = nn.Linear(input_size, hidden_size, bias=False)
        self.h2h = nn.Linear(hidden_size, hidden_size)
        self.score = nn.Linear(hidden_size, 1, bias=False)
        self.rnn = nn.GRUCell(input_size + num_classes, hidden_size)
        self.hidden_size = hidden_size

    def forward(self, prev_hidden, batch_H, char_onehots):
        batch_H_proj = self.i2h(batch_H)
        prev_hidden_proj = self.h2h(prev_hidden).unsqueeze(1)
        e = self.score(torch.tanh(batch_H_proj + prev_hidden_proj))  # batch_size x num_encoder_step * 1
        
        alpha = F.softmax(e, dim=1)
        context = torch.bmm(alpha.permute(0, 2, 1), batch_H).squeeze(1)  # batch_size x num_channel
        concat_context = torch.cat([context, char_onehots], 1)  # batch_size x (num_channel + num_classes)
        cur_hidden = self.rnn(concat_context, prev_hidden)
        return cur_hidden, alpha


class Attention(nn.Module):
    """Attention-based sequence prediction"""
    
    def __init__(self, input_size, hidden_size, num_classes, device):
        super(Attention, self).__init__()
        self.attention_cell = AttentionCell(input_size, hidden_size, num_classes)
        self.hidden_size = hidden_size
        self.num_classes = num_classes
        self.generator = nn.Linear(hidden_size, num_classes)
        self.device = device

    def _char_to_onehot(self, char_tensors, onehot_dim):
        batch_size = char_tensors.size(0)
        onehot = torch.zeros(batch_size, onehot_dim).to(self.device)
        onehot.scatter_(1, char_tensors, 1)
        return onehot

    def forward(self, batch_H, text, is_train=True, batch_max_length=25):
        batch_size = batch_H.size(0)
        num_steps = batch_max_length

        output_hiddens = torch.zeros(batch_size, num_steps, self.hidden_size).to(self.device)
        hidden = torch.zeros(batch_size, self.hidden_size).to(self.device)

        if is_train:
            for i in range(num_steps):
                char_onehots = self._char_to_onehot(text[:, i], onehot_dim=self.num_classes)
                hidden, alpha = self.attention_cell(hidden, batch_H, char_onehots)
                output_hiddens[:, i, :] = hidden  # BATCHSIZE x num_steps x HIDDENSIZE
            probs = self.generator(output_hiddens)  # BATCHSIZE x num_steps x num_classes

        else:
            targets = torch.zeros(batch_size).long().to(self.device)  # [GO] token
            probs = torch.zeros(batch_size, num_steps, self.num_classes).to(self.device)

            for i in range(num_steps):
                char_onehots = self._char_to_onehot(targets, onehot_dim=self.num_classes)
                hidden, alpha = self.attention_cell(hidden, batch_H, char_onehots)
                probs_step = self.generator(hidden)
                probs[:, i, :] = probs_step
                next_input = probs_step.argmax(dim=1)
                targets = next_input

        return probs


class CRNNNet(nn.Module):
    """
    CRNN Network for Text Recognition
    CNN + RNN + CTC for sequence-to-sequence learning
    """
    
    def __init__(self, 
                 img_h, 
                 img_w, 
                 num_class, 
                 num_channel=1, 
                 feature_extractor='ResNet', 
                 prediction='CTC',
                 max_text_length=25,
                 device='cuda'):
        
        super(CRNNNet, self).__init__()
        
        self.img_h = img_h
        self.img_w = img_w
        self.num_class = num_class
        self.max_text_length = max_text_length
        self.device = device
        self.prediction = prediction
        
        # Feature extraction
        if feature_extractor == 'ResNet':
            self.feature_extractor = ResNet_FeatureExtractor(num_channel, 512)
        else:
            raise ValueError(f'Unknown feature extractor: {feature_extractor}')
        
        self.feature_extractor_output_dim = 512
        
        # Sequence modeling
        self.sequence_modeling = nn.Sequential(
            BidirectionalLSTM(self.feature_extractor_output_dim, 256, 256),
            BidirectionalLSTM(256, 256, 256)
        )
        self.sequence_modeling_output_dim = 256
        
        # Prediction
        if prediction == 'CTC':
            self.prediction_layer = nn.Linear(self.sequence_modeling_output_dim, num_class)
        elif prediction == 'Attention':
            self.prediction_layer = Attention(
                self.sequence_modeling_output_dim, 256, num_class, device
            )
        else:
            raise ValueError(f'Unknown prediction method: {prediction}')

    def forward(self, input, text=None, is_train=True):
        """Forward pass through CRNN"""
        
        # Feature extraction
        visual_feature = self.feature_extractor(input)  # [b, c, h, w]
        visual_feature = visual_feature.permute(0, 3, 1, 2)  # [b, w, c, h]
        
        b, w, c, h = visual_feature.size()
        visual_feature = visual_feature.view(b, w, c * h)
        
        # Ensure feature dimension matches expected input
        if visual_feature.size(2) != self.feature_extractor_output_dim:
            # Add adaptive layer if dimension mismatch
            if not hasattr(self, 'adaptive_layer'):
                self.adaptive_layer = nn.Linear(visual_feature.size(2), self.feature_extractor_output_dim).to(visual_feature.device)
            visual_feature = self.adaptive_layer(visual_feature)
        
        # Sequence modeling
        contextual_feature = self.sequence_modeling(visual_feature)  # [b, w, c]
        
        # Prediction
        if self.prediction == 'CTC':
            prediction = self.prediction_layer(contextual_feature)  # [b, w, num_class]
            prediction = F.log_softmax(prediction, dim=2)
        elif self.prediction == 'Attention':
            prediction = self.prediction_layer(
                contextual_feature, text, is_train, self.max_text_length
            )
        
        return prediction


class CTCLoss(nn.Module):
    """CTC Loss with label smoothing"""
    
    def __init__(self, blank_idx=0, reduction='mean', zero_infinity=True):
        super(CTCLoss, self).__init__()
        self.blank_idx = blank_idx
        self.ctc_loss = nn.CTCLoss(
            blank=blank_idx, 
            reduction=reduction, 
            zero_infinity=zero_infinity
        )

    def forward(self, log_probs, targets, input_lengths, target_lengths):
        """
        Args:
            log_probs: (T, N, C) log probabilities from model
            targets: (sum(target_lengths)) target sequences (concatenated)
            input_lengths: (N) input sequence lengths
            target_lengths: (N) target sequence lengths
        """
        # Transpose to get (T, N, C) format for CTC loss
        log_probs = log_probs.permute(1, 0, 2)
        
        loss = self.ctc_loss(log_probs, targets, input_lengths, target_lengths)
        return loss


class LabelConverter:
    """Convert between text and label indices"""
    
    def __init__(self, character_set=None, use_space=True):
        if character_set is None:
            # Default character set for IC markings
            self.character = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        else:
            self.character = character_set
        
        if use_space:
            self.character = ' ' + self.character
        
        # Add special tokens
        self.character = '[CTCblank]' + self.character + '[UNK]'
        
        self.dict = {char: i for i, char in enumerate(self.character)}
        self.character = list(self.character)
    
    def encode(self, text_batch, batch_max_length=25):
        """Convert text to label indices"""
        batch_size = len(text_batch)
        length_list = []
        
        for text in text_batch:
            length_list.append(len(text))
        
        batch_max_length = max(length_list)
        
        # Initialize with UNK token
        unk_idx = len(self.character) - 1
        batch_text = torch.LongTensor(batch_size, batch_max_length).fill_(unk_idx)
        
        for i, text in enumerate(text_batch):
            text = text.upper()  # Convert to uppercase
            for j, char in enumerate(text):
                if char in self.dict:
                    batch_text[i][j] = self.dict[char]
                else:
                    batch_text[i][j] = unk_idx  # UNK token
        
        return batch_text, torch.IntTensor(length_list)
    
    def decode(self, text_index, length):
        """Convert label indices to text"""
        if len(text_index.shape) > 1:
            # Batch decoding
            texts = []
            for i in range(text_index.shape[0]):
                l = length[i] if length is not None else len(text_index[i])
                text = ''.join([
                    self.character[idx] 
                    for idx in text_index[i][:l] 
                    if idx < len(self.character)
                ])
                texts.append(text)
            return texts
        else:
            # Single text decoding
            l = length if length is not None else len(text_index)
            return ''.join([
                self.character[idx] 
                for idx in text_index[:l] 
                if idx < len(self.character)
            ])


class CRNNRecognizer:
    """
    CRNN Text Recognizer with preprocessing and post-processing
    """
    
    def __init__(self, 
                 model_path=None,
                 img_h=64, 
                 img_w=256,
                 character_set=None,
                 device='cuda',
                 prediction='CTC'):
        
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.img_h = img_h
        self.img_w = img_w
        self.prediction = prediction
        
        # Initialize label converter
        self.converter = LabelConverter(character_set)
        num_class = len(self.converter.character)
        
        # Initialize model
        self.model = CRNNNet(
            img_h=img_h,
            img_w=img_w,
            num_class=num_class,
            device=self.device,
            prediction=prediction
        ).to(self.device)
        
        if model_path:
            self.load_model(model_path)
        
        self.model.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((img_h, img_w)),
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])
    
    def load_model(self, model_path):
        """Load pretrained CRNN model"""
        print(f'Loading CRNN model from {model_path}')
        
        if self.device == 'cpu':
            state_dict = torch.load(model_path, map_location='cpu')
        else:
            state_dict = torch.load(model_path)
        
        # Handle different state dict formats
        if 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        elif 'model' in state_dict:
            state_dict = state_dict['model']
        
        # Remove 'module.' prefix if present
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:] if k.startswith('module.') else k
            new_state_dict[name] = v
        
        self.model.load_state_dict(new_state_dict, strict=False)
        print('CRNN model loaded successfully')
    
    def preprocess_image(self, image):
        """Preprocess image for recognition"""
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Normalize height while maintaining aspect ratio
        h, w = image.shape
        aspect_ratio = w / h
        
        if aspect_ratio > self.img_w / self.img_h:
            # Width is the limiting factor
            new_w = self.img_w
            new_h = int(self.img_w / aspect_ratio)
        else:
            # Height is the limiting factor
            new_h = self.img_h
            new_w = int(self.img_h * aspect_ratio)
        
        # Resize image
        resized = cv2.resize(image, (new_w, new_h))
        
        # Pad to target size
        padded = np.ones((self.img_h, self.img_w), dtype=np.uint8) * 255
        y_offset = (self.img_h - new_h) // 2
        x_offset = (self.img_w - new_w) // 2
        padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        # Convert to tensor
        tensor = self.transform(padded).unsqueeze(0)
        
        return tensor
    
    def recognize_text(self, image_tensor):
        """Recognize text from preprocessed image tensor"""
        
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            
            if self.prediction == 'CTC':
                preds = self.model(image_tensor, text=None, is_train=False)
                
                # CTC decoding
                preds_size = torch.IntTensor([preds.size(1)] * preds.size(0))
                _, preds_index = preds.max(2)
                
                # Remove repeated characters and blank
                preds_str = []
                for i in range(preds.size(0)):
                    pred_EOS = preds_size[i]
                    pred_index = preds_index[i][:pred_EOS]
                    
                    # CTC decoding: remove repeated chars and blanks
                    char_list = []
                    prev_char = -1
                    for char_idx in pred_index:
                        char_idx = char_idx.item()
                        if char_idx != 0 and char_idx != prev_char:  # 0 is blank
                            if char_idx < len(self.converter.character):
                                char_list.append(self.converter.character[char_idx])
                        prev_char = char_idx
                    
                    pred_str = ''.join(char_list)
                    preds_str.append(pred_str)
                
            elif self.prediction == 'Attention':
                preds = self.model(image_tensor, text=None, is_train=False)
                
                # Attention decoding
                _, preds_index = preds.max(2)
                preds_str = self.converter.decode(preds_index, None)
                
                # Clean up predictions (remove special tokens)
                cleaned_preds = []
                for pred_str in preds_str:
                    # Remove special tokens and clean up
                    cleaned = pred_str.replace('[CTCblank]', '').replace('[UNK]', '')
                    cleaned_preds.append(cleaned.strip())
                preds_str = cleaned_preds
            
            # Calculate confidence scores (simplified)
            confidence_scores = []
            for i in range(preds.size(0)):
                # Average of max probabilities
                probs = F.softmax(preds[i], dim=1)
                max_probs = probs.max(dim=1)[0]
                confidence = max_probs.mean().item()
                confidence_scores.append(confidence)
        
        return preds_str, confidence_scores
    
    def recognize_from_image(self, image):
        """End-to-end recognition from raw image"""
        
        # Preprocess
        image_tensor = self.preprocess_image(image)
        
        # Recognize
        texts, confidences = self.recognize_text(image_tensor)
        
        return texts[0] if len(texts) > 0 else "", confidences[0] if len(confidences) > 0 else 0.0
    
    def batch_recognize(self, image_list):
        """Batch recognition for multiple images"""
        
        # Preprocess all images
        batch_tensors = []
        for image in image_list:
            tensor = self.preprocess_image(image)
            batch_tensors.append(tensor)
        
        # Stack into batch
        batch_tensor = torch.cat(batch_tensors, dim=0)
        
        # Recognize batch
        texts, confidences = self.recognize_text(batch_tensor)
        
        return texts, confidences


# Curriculum Learning utilities for character quality
class CurriculumLearningScheduler:
    """Scheduler for curriculum learning based on character quality"""
    
    def __init__(self, 
                 start_epoch=0, 
                 easy_epochs=10, 
                 medium_epochs=20, 
                 hard_epochs=30):
        self.start_epoch = start_epoch
        self.easy_epochs = easy_epochs
        self.medium_epochs = medium_epochs
        self.hard_epochs = hard_epochs
    
    def get_difficulty_weights(self, epoch):
        """Get difficulty weights based on current epoch"""
        
        if epoch < self.easy_epochs:
            # Only easy samples
            return {'high': 1.0, 'medium': 0.0, 'low': 0.0}
        elif epoch < self.medium_epochs:
            # Easy + medium samples
            progress = (epoch - self.easy_epochs) / (self.medium_epochs - self.easy_epochs)
            return {'high': 1.0, 'medium': progress, 'low': 0.0}
        elif epoch < self.hard_epochs:
            # All samples with increasing hard weight
            progress = (epoch - self.medium_epochs) / (self.hard_epochs - self.medium_epochs)
            return {'high': 1.0, 'medium': 1.0, 'low': progress}
        else:
            # All samples equally
            return {'high': 1.0, 'medium': 1.0, 'low': 1.0}


if __name__ == "__main__":
    # Test CRNN recognizer
    recognizer = CRNNRecognizer(device='cpu')  # Use CPU for testing
    
    # Create dummy image
    test_image = np.random.randint(0, 255, (64, 256), dtype=np.uint8)
    
    # Recognize text
    text, confidence = recognizer.recognize_from_image(test_image)
    
    print(f"Recognized text: '{text}'")
    print(f"Confidence: {confidence:.3f}")
    
    print("CRNN recognizer test completed")