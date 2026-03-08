import torch
import time

print(f'PyTorch: {torch.__version__}')
print(f'CUDA dostępne: {torch.cuda.is_available()}')
print(f'Karta: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')

rozmiar = 4096
a = torch.randn(rozmiar, rozmiar)
b = torch.randn(rozmiar, rozmiar)

start = time.time()
for _ in range(10):
    c = a @ b
cpu_czas = time.time() - start

a = a.cuda()
b = b.cuda()
torch.cuda.synchronize()
start = time.time()
for _ in range(10):
    c = a @ b
torch.cuda.synchronize()
gpu_czas = time.time() - start

print(f'CPU: {cpu_czas:.2f}s')
print(f'GPU: {gpu_czas:.2f}s')
print(f'Przyspieszenie: {cpu_czas/gpu_czas:.0f}x')