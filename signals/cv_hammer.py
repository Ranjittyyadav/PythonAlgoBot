"""
Computer vision-based bullish hammer signal engine.
"""
import logging
import os
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from typing import List, Dict, Any, Optional
from pathlib import Path

from signals.base import SignalEngine
from charting.renderer import render_candles_to_image
from models.cv_model import load_cv_model
import config

logger = logging.getLogger(__name__)


class CVHammerSignalEngine(SignalEngine):
    """Signal engine that detects bullish hammer patterns using computer vision."""
    
    def __init__(
        self,
        model_weights_path: str,
        device: Optional[torch.device] = None,
        threshold: float = 0.7,
        image_dir: str = "chart_images"
    ):
        """
        Initialize CV-based hammer signal engine.
        
        Args:
            model_weights_path: Path to trained model weights
            device: PyTorch device (CPU or CUDA). If None, auto-detect.
            threshold: Confidence threshold for buy signal (0.0 to 1.0)
            image_dir: Directory to save rendered chart images
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.device = device
        self.threshold = threshold
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model
        self.model = load_cv_model(model_weights_path, self.device)
        
        # Image preprocessing transforms (matching ImageNet normalization)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info(f"Initialized CVHammerSignalEngine (device={device}, threshold={threshold})")
    
    def generate_signal(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate signal using computer vision model.
        
        Args:
            candles: List of candle dictionaries
            
        Returns:
            Signal dictionary with is_buy, pattern, and score
        """
        if len(candles) == 0:
            return {"is_buy": False, "pattern": None, "score": 0.0}
        
        try:
            # Render candles to image
            image_path = self.image_dir / "current_chart.png"
            render_candles_to_image(candles, str(image_path), last_n=40)
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = F.softmax(outputs, dim=1)
                hammer_prob = probabilities[0][1].item()  # Class 1 = hammer
            
            # Make decision
            is_buy = hammer_prob >= self.threshold
            
            logger.info(f"CV signal: hammer_prob={hammer_prob:.3f}, threshold={self.threshold}, is_buy={is_buy}")
            
            return {
                "is_buy": is_buy,
                "pattern": "bullish_hammer_cv" if is_buy else None,
                "score": hammer_prob
            }
        except Exception as e:
            logger.error(f"Error generating CV signal: {e}")
            return {"is_buy": False, "pattern": None, "score": 0.0}

