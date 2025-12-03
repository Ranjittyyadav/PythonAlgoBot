"""
Computer vision model for candlestick pattern classification.
"""
import logging
import torch
import torch.nn as nn
from torchvision import models
from typing import Optional

logger = logging.getLogger(__name__)


def create_cv_model(num_classes: int = 2, pretrained: bool = True) -> nn.Module:
    """
    Create a CNN model for candlestick pattern classification.
    
    Uses a ResNet18 backbone for transfer learning.
    
    Args:
        num_classes: Number of output classes (default: 2 for binary classification)
        pretrained: Whether to use pretrained weights (default: True)
        
    Returns:
        PyTorch model
    """
    try:
        # Try using the new weights API (torchvision >= 0.13)
        from torchvision.models import ResNet18_Weights
        if pretrained:
            model = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        else:
            model = models.resnet18(weights=None)
    except (ImportError, AttributeError):
        # Fallback to old API or if weights not available
        try:
            model = models.resnet18(pretrained=pretrained)
        except Exception as e:
            logger.warning(f"Could not load pretrained weights: {e}. Using untrained model.")
            model = models.resnet18(pretrained=False)
    
    # Replace the final fully connected layer
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    
    logger.info(f"Created CV model with {num_classes} classes (pretrained={pretrained})")
    return model


def load_cv_model(weights_path: str, device: torch.device, num_classes: int = 2) -> nn.Module:
    """
    Load a trained CV model from weights file.
    
    Args:
        weights_path: Path to the model weights file
        device: PyTorch device (CPU or CUDA)
        num_classes: Number of output classes
        
    Returns:
        Loaded PyTorch model in eval mode
    """
    model = create_cv_model(num_classes=num_classes, pretrained=False)
    
    try:
        checkpoint = torch.load(weights_path, map_location=device)
        
        # Handle different checkpoint formats
        if isinstance(checkpoint, dict):
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            elif 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
            else:
                model.load_state_dict(checkpoint)
        else:
            model.load_state_dict(checkpoint)
        
        model.to(device)
        model.eval()
        logger.info(f"Loaded CV model from {weights_path}")
        return model
    except Exception as e:
        logger.error(f"Error loading model from {weights_path}: {e}")
        raise

