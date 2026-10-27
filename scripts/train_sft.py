"""
Domain Supervised Fine-Tuning CLI script for EmbeddedCoder AI.
"""

import argparse
import yaml
from pathlib import Path
from embeddedcoder.core.config import SFTConfig
from embeddedcoder.training.trainer import train_sft
from embeddedcoder.core.constants import CONFIGS_DIR


def parse_args():
    parser = argparse.ArgumentParser(description="Run SFT fine-tuning on embedded engineering dataset")
    parser.add_argument(
        "--config", 
        type=str, 
        default=str(CONFIGS_DIR / "sft.yaml"),
        help="Path to SFT YAML config"
    )
    parser.add_argument("--epochs", type=int, default=None, help="Override number of epochs")
    parser.add_argument("--batch_size", type=int, default=None, help="Override per_device_train_batch_size")
    parser.add_argument("--output_dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config)
    
    with open(config_path, "r", encoding="utf-8") as f:
        cfg_dict = yaml.safe_load(f)

    if args.epochs:
        cfg_dict["num_train_epochs"] = args.epochs
    if args.batch_size:
        cfg_dict["per_device_train_batch_size"] = args.batch_size
    if args.output_dir:
        cfg_dict["output_dir"] = args.output_dir

    config = SFTConfig(**cfg_dict)
    train_sft(config)


if __name__ == "__main__":
    main()
