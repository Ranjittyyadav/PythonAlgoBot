"""
Training script for the computer vision candlestick pattern classifier.
"""
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
from pathlib import Path
import argparse

from models.cv_model import create_cv_model
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CandlestickDataset(Dataset):
    """Dataset for candlestick pattern images."""
    
    def __init__(self, data_dir: str, transform=None):
        """
        Initialize dataset.
        
        Args:
            data_dir: Root directory containing 'hammer' and 'none' subdirectories
            transform: Image transforms to apply
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        
        # Collect all image paths with labels
        self.samples = []
        
        # Class 0: no hammer
        none_dir = self.data_dir / "none"
        if none_dir.exists():
            for img_path in none_dir.glob("*.png"):
                self.samples.append((img_path, 0))
        
        # Class 1: hammer
        hammer_dir = self.data_dir / "hammer"
        if hammer_dir.exists():
            for img_path in hammer_dir.glob("*.png"):
                self.samples.append((img_path, 1))
        
        logger.info(f"Loaded {len(self.samples)} samples from {data_dir}")
        logger.info(f"  - No hammer (class 0): {sum(1 for _, label in self.samples if label == 0)}")
        logger.info(f"  - Hammer (class 1): {sum(1 for _, label in self.samples if label == 1)}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    """Validate the model."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc


def main():
    parser = argparse.ArgumentParser(description="Train CV model for candlestick pattern classification")
    parser.add_argument("--data_dir", type=str, default="data/train", help="Training data directory")
    parser.add_argument("--val_dir", type=str, default="data/val", help="Validation data directory")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--output", type=str, default=config.CV_MODEL_WEIGHTS, help="Output model path")
    
    args = parser.parse_args()
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # Data transforms
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(5),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create datasets
    train_dataset = CandlestickDataset(args.data_dir, transform=train_transform)
    val_dataset = CandlestickDataset(args.val_dir, transform=val_transform) if Path(args.val_dir).exists() else None
    
    if len(train_dataset) == 0:
        logger.error(f"No training data found in {args.data_dir}")
        logger.error("Expected directory structure:")
        logger.error("  data/train/hammer/*.png")
        logger.error("  data/train/none/*.png")
        return
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False) if val_dataset else None
    
    # Create model
    # Try pretrained first, fallback to untrained if download fails
    try:
        model = create_cv_model(num_classes=2, pretrained=True)
    except Exception as e:
        logger.warning(f"Failed to load pretrained model: {e}")
        logger.info("Falling back to untrained model (training will take longer)")
        model = create_cv_model(num_classes=2, pretrained=False)
    model = model.to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # Training loop
    best_val_acc = 0.0
    
    for epoch in range(args.epochs):
        logger.info(f"\nEpoch {epoch + 1}/{args.epochs}")
        logger.info("-" * 40)
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        logger.info(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        
        # Validate
        if val_loader:
            val_loss, val_acc = validate(model, val_loader, criterion, device)
            logger.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_acc': val_acc,
                }, args.output)
                logger.info(f"Saved best model to {args.output} (val_acc: {val_acc:.2f}%)")
        else:
            # Save model after each epoch if no validation set
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
            }, args.output)
            logger.info(f"Saved model to {args.output}")
    
    logger.info("\nTraining completed!")


if __name__ == "__main__":
    main()

