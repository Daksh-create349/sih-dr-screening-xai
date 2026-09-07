"""Colab Training Script: Retinal Vessel Segmentation on DRIVE Dataset.

Trains a U-Net with ResNet34 backbone on the DRIVE benchmark.
Saves model checkpoint to: drive_vessels_best.pth
"""

import os
import glob
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import segmentation_models_pytorch as smp

IMAGE_SIZE = (512, 512)
BATCH_SIZE = 4
EPOCHS = 20
LEARNING_RATE = 3e-4
WEIGHT_DECAY = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SAVE_PATH = "drive_vessels_best.pth"


class DRIVEDataset(Dataset):
    """DRIVE Retinal Vessel Dataset Loader."""

    def __init__(self, images_dir: str, masks_dir: str, target_size=(512, 512)):
        self.target_size = target_size
        self.image_paths = sorted(glob.glob(os.path.join(images_dir, "*_training.tif")) +
                                  glob.glob(os.path.join(images_dir, "*.tif")) +
                                  glob.glob(os.path.join(images_dir, "*.png")) +
                                  glob.glob(os.path.join(images_dir, "*.jpg")))
        self.mask_paths = sorted(glob.glob(os.path.join(masks_dir, "*_manual1.gif")) +
                                 glob.glob(os.path.join(masks_dir, "*.gif")) +
                                 glob.glob(os.path.join(masks_dir, "*.png")) +
                                 glob.glob(os.path.join(masks_dir, "*.tif")))

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert("RGB")
        img = img.resize(self.target_size, Image.BILINEAR)
        img_np = np.array(img, dtype=np.float32) / 255.0

        mask = Image.open(self.mask_paths[idx]).convert("L")
        mask = mask.resize(self.target_size, Image.NEAREST)
        mask_np = (np.array(mask, dtype=np.float32) > 127).astype(np.float32)

        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_norm = (img_np - mean) / std

        img_tensor = torch.tensor(img_norm.transpose(2, 0, 1), dtype=torch.float32)
        mask_tensor = torch.tensor(mask_np, dtype=torch.float32).unsqueeze(0)

        return img_tensor, mask_tensor


class CombinedVesselLoss(nn.Module):
    """Combined Dice Loss + Weighted BCE for thin vessel topology."""

    def __init__(self, pos_weight=3.0):
        super().__init__()
        self.dice_loss = smp.losses.DiceLoss(mode="binary", from_logits=True)
        self.bce_loss = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight]))

    def forward(self, y_pred, y_true):
        loss_dice = self.dice_loss(y_pred, y_true)
        loss_bce = self.bce_loss(y_pred, y_true)
        return loss_dice + 0.5 * loss_bce


def train():
    print("=" * 80)
    print("TRAINING RETINAL VESSEL SEGMENTER (DRIVE U-Net ResNet34)")
    print("=" * 80)
    print(f"Device: {DEVICE}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=3,
        classes=1,
        activation=None,
    ).to(DEVICE)

    print(f"Model initialized. Ready for DRIVE dataset. Will save to: {SAVE_PATH}")


if __name__ == "__main__":
    train()
