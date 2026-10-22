"""Device policy shared by the least-squares and end-to-end entry points (CPU and CUDA only)."""
import torch

SUPPORTED_DEVICE_TYPES = ("cpu", "cuda")


def require_supported_device(device: torch.device, what: str) -> None:
    if device.type not in SUPPORTED_DEVICE_TYPES:
        raise ValueError(
            f"{what} must be on a CPU or CUDA device, got device {device}; other devices are not supported"
        )


def same_device(a: torch.device, b: torch.device) -> bool:
    """Equal device types and, for CUDA, equal indices (an unset index means the current device)."""
    if a.type != b.type:
        return False
    if a.type == "cuda":
        current = torch.cuda.current_device() if torch.cuda.is_available() else 0
        return (current if a.index is None else a.index) == (current if b.index is None else b.index)
    return a == b


def lstsq_driver(device: torch.device) -> str:
    """CPU keeps the rank-revealing SVD driver; CUDA only supports ``gels``, which assumes full rank."""
    return "gelsd" if device.type == "cpu" else "gels"


def check_generator(generator, device: torch.device) -> None:
    """A generator must live on the tensor's device (validated before any random draw)."""
    if generator is not None and not same_device(generator.device, device):
        raise ValueError(f"generator is on device {generator.device} but a is on {device}; they must match")


def check_distribution(distribution: str, device: torch.device) -> None:
    """Only the Gaussian test matrices are in the accelerator contract."""
    if device.type == "cuda" and distribution.lower() != "gaussian":
        raise ValueError(
            f"distribution {distribution!r} is not validated on CUDA; only 'gaussian' is supported there"
        )
