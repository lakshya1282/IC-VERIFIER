#!/usr/bin/env python3
"""
GPU Performance Test Script for IC Verification System
Tests and compares CPU vs GPU performance for deep learning inference
"""

import os
import sys
import time
import torch
import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import json

# Import our IC pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_real_pipeline import RealDatasetICRecognitionPipeline

def generate_test_images(num_images=10, size=(224, 224, 3)):
    """Generate test IC images for benchmarking"""
    images = []
    for i in range(num_images):
        # Create synthetic IC-like image
        img = np.random.randint(0, 255, size, dtype=np.uint8)
        
        # Add some IC-like features
        # Add rectangular regions (simulating IC packages)
        h, w = size[:2]
        cv2.rectangle(img, (20, 20), (w-20, h-20), (50, 50, 50), 2)
        cv2.rectangle(img, (40, 40), (w-40, h-40), (200, 200, 200), -1)
        
        # Add some text-like regions
        cv2.putText(img, f"IC{i:03d}", (50, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "STM32", (50, h//2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        images.append(img)
    
    return images

def benchmark_inference_speed(pipeline, images, device_name):
    """Benchmark inference speed on given device"""
    print(f"\n🧪 Benchmarking inference speed on {device_name}...")
    
    times = []
    results = []
    
    # Warmup (important for GPU)
    print("   🔥 Warming up...")
    for i in range(min(3, len(images))):
        _ = pipeline.process_image(images[i], save_results=False)
    
    # Actual benchmarking
    print(f"   ⏱️ Running {len(images)} inference tests...")
    
    start_total = time.time()
    
    for i, image in enumerate(images):
        start_time = time.time()
        result = pipeline.process_image(image, save_results=False)
        end_time = time.time()
        
        inference_time = end_time - start_time
        times.append(inference_time)
        results.append(result)
        
        print(f"     Image {i+1}/{len(images)}: {inference_time:.3f}s")
    
    end_total = time.time()
    total_time = end_total - start_total
    
    # Calculate statistics
    avg_time = np.mean(times)
    min_time = np.min(times)
    max_time = np.max(times)
    std_time = np.std(times)
    throughput = len(images) / total_time
    
    print(f"\n📊 {device_name} Performance Results:")
    print(f"   • Average inference time: {avg_time:.3f}s")
    print(f"   • Min inference time: {min_time:.3f}s")
    print(f"   • Max inference time: {max_time:.3f}s")
    print(f"   • Standard deviation: {std_time:.3f}s")
    print(f"   • Total time: {total_time:.3f}s")
    print(f"   • Throughput: {throughput:.2f} images/sec")
    
    return {
        'device': device_name,
        'times': times,
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'std_time': std_time,
        'total_time': total_time,
        'throughput': throughput,
        'results': results
    }

def compare_cpu_gpu_performance():
    """Compare CPU vs GPU performance"""
    print("🚀 IC Verification System GPU Performance Test")
    print("=" * 60)
    
    # Check GPU availability
    if not torch.cuda.is_available():
        print("❌ CUDA not available. Cannot run GPU performance test.")
        return
    
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    
    print(f"🖥️ System Information:")
    print(f"   • CPU: Available")
    print(f"   • GPU: {gpu_name}")
    print(f"   • GPU Memory: {gpu_memory:.1f} GB")
    print(f"   • PyTorch Version: {torch.__version__}")
    print(f"   • CUDA Version: {torch.version.cuda}")
    
    # Generate test images
    print(f"\n🎨 Generating test images...")
    test_images = generate_test_images(num_images=20)
    print(f"   Generated {len(test_images)} test images")
    
    # Test GPU performance (current default)
    gpu_pipeline = RealDatasetICRecognitionPipeline(model_path="./models/real_trained/best_verification_real.pth")
    gpu_results = benchmark_inference_speed(gpu_pipeline, test_images, f"GPU ({gpu_name})")
    
    # Force CPU mode for comparison
    print(f"\n🔄 Switching to CPU mode for comparison...")
    original_device = torch.cuda.is_available
    
    # Temporarily disable CUDA for CPU test
    torch.cuda.is_available = lambda: False
    cpu_pipeline = RealDatasetICRecognitionPipeline(model_path="./models/real_trained/best_verification_real.pth")
    cpu_results = benchmark_inference_speed(cpu_pipeline, test_images, "CPU")
    
    # Restore CUDA availability
    torch.cuda.is_available = original_device
    
    # Compare results
    print(f"\n🏆 Performance Comparison:")
    print(f"{'Metric':<25} {'CPU':<15} {'GPU':<15} {'Speedup':<15}")
    print("-" * 70)
    
    speedup_avg = cpu_results['avg_time'] / gpu_results['avg_time']
    speedup_throughput = gpu_results['throughput'] / cpu_results['throughput']
    
    print(f"{'Average Time (s)':<25} {cpu_results['avg_time']:<15.3f} {gpu_results['avg_time']:<15.3f} {speedup_avg:<15.2f}x")
    print(f"{'Min Time (s)':<25} {cpu_results['min_time']:<15.3f} {gpu_results['min_time']:<15.3f} {cpu_results['min_time']/gpu_results['min_time']:<15.2f}x")
    print(f"{'Throughput (img/s)':<25} {cpu_results['throughput']:<15.2f} {gpu_results['throughput']:<15.2f} {speedup_throughput:<15.2f}x")
    
    # Memory usage comparison
    if torch.cuda.is_available():
        gpu_memory_used = torch.cuda.max_memory_allocated() / 1024**3
        print(f"{'GPU Memory Used (GB)':<25} {'N/A':<15} {gpu_memory_used:<15.2f} {'-':<15}")
    
    # Save results
    results_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'system_info': {
            'gpu_name': gpu_name,
            'gpu_memory_gb': gpu_memory,
            'pytorch_version': torch.__version__,
            'cuda_version': torch.version.cuda
        },
        'cpu_results': cpu_results,
        'gpu_results': gpu_results,
        'performance_improvement': {
            'speed_improvement': speedup_avg,
            'throughput_improvement': speedup_throughput
        }
    }
    
    # Remove non-serializable data
    for result_set in ['cpu_results', 'gpu_results']:
        if 'results' in results_data[result_set]:
            del results_data[result_set]['results']
        results_data[result_set]['times'] = [float(t) for t in results_data[result_set]['times']]
    
    with open('gpu_performance_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n💾 Results saved to: gpu_performance_results.json")
    
    # Create visualization
    create_performance_visualization(cpu_results, gpu_results)
    
    print(f"\n🎯 Summary:")
    print(f"   • GPU provides {speedup_avg:.2f}x faster inference than CPU")
    print(f"   • GPU achieves {speedup_throughput:.2f}x higher throughput")
    if speedup_avg > 2.0:
        print(f"   • 🚀 Excellent GPU acceleration! Significant performance boost achieved.")
    elif speedup_avg > 1.5:
        print(f"   • ⚡ Good GPU acceleration. Notable performance improvement.")
    else:
        print(f"   • 💡 Moderate GPU acceleration. May benefit from optimization.")

def create_performance_visualization(cpu_results, gpu_results):
    """Create performance comparison charts"""
    try:
        plt.style.use('seaborn-v0_8')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('IC Verification System: CPU vs GPU Performance', fontsize=16, fontweight='bold')
        
        # 1. Inference Time Comparison (Bar Chart)
        ax1.bar(['CPU', 'GPU'], [cpu_results['avg_time'], gpu_results['avg_time']], 
                color=['#ff7f0e', '#2ca02c'], alpha=0.7)
        ax1.set_ylabel('Average Inference Time (seconds)')
        ax1.set_title('Average Inference Time Comparison')
        for i, v in enumerate([cpu_results['avg_time'], gpu_results['avg_time']]):
            ax1.text(i, v + 0.01, f'{v:.3f}s', ha='center', va='bottom')
        
        # 2. Throughput Comparison
        ax2.bar(['CPU', 'GPU'], [cpu_results['throughput'], gpu_results['throughput']], 
                color=['#ff7f0e', '#2ca02c'], alpha=0.7)
        ax2.set_ylabel('Throughput (images/second)')
        ax2.set_title('Throughput Comparison')
        for i, v in enumerate([cpu_results['throughput'], gpu_results['throughput']]):
            ax2.text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom')
        
        # 3. Inference Time Distribution
        ax3.hist([cpu_results['times'], gpu_results['times']], 
                bins=10, alpha=0.7, label=['CPU', 'GPU'], color=['#ff7f0e', '#2ca02c'])
        ax3.set_xlabel('Inference Time (seconds)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Inference Time Distribution')
        ax3.legend()
        
        # 4. Performance Metrics Summary
        metrics = ['Avg Time', 'Min Time', 'Max Time', 'Std Dev']
        cpu_values = [cpu_results['avg_time'], cpu_results['min_time'], 
                     cpu_results['max_time'], cpu_results['std_time']]
        gpu_values = [gpu_results['avg_time'], gpu_results['min_time'], 
                     gpu_results['max_time'], gpu_results['std_time']]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax4.bar(x - width/2, cpu_values, width, label='CPU', color='#ff7f0e', alpha=0.7)
        ax4.bar(x + width/2, gpu_values, width, label='GPU', color='#2ca02c', alpha=0.7)
        
        ax4.set_xlabel('Metrics')
        ax4.set_ylabel('Time (seconds)')
        ax4.set_title('Performance Metrics Summary')
        ax4.set_xticks(x)
        ax4.set_xticklabels(metrics)
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig('gpu_performance_comparison.png', dpi=300, bbox_inches='tight')
        print(f"📊 Performance visualization saved to: gpu_performance_comparison.png")
        
    except ImportError:
        print("📊 Matplotlib not available. Skipping visualization.")
    except Exception as e:
        print(f"📊 Could not create visualization: {e}")

def test_memory_usage():
    """Test GPU memory usage during inference"""
    if not torch.cuda.is_available():
        print("❌ GPU not available for memory test")
        return
    
    print("\n🧠 GPU Memory Usage Test:")
    
    # Clear cache
    torch.cuda.empty_cache()
    
    print(f"   • Initial GPU Memory: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
    
    # Initialize pipeline
    pipeline = RealDatasetICRecognitionPipeline(model_path="./models/real_trained/best_verification_real.pth")
    print(f"   • After Pipeline Init: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
    
    # Generate test image
    test_image = generate_test_images(1)[0]
    
    # Run inference
    result = pipeline.process_image(test_image, save_results=False)
    print(f"   • After Inference: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
    print(f"   • Peak GPU Memory: {torch.cuda.max_memory_allocated() / 1024**2:.1f} MB")
    
    # Memory efficiency
    total_gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**2
    memory_usage_percent = (torch.cuda.max_memory_allocated() / 1024**2) / total_gpu_memory * 100
    print(f"   • Memory Usage: {memory_usage_percent:.1f}% of total GPU memory")

if __name__ == "__main__":
    try:
        compare_cpu_gpu_performance()
        test_memory_usage()
        
        print(f"\n✅ GPU Performance Test Completed!")
        print(f"📁 Results saved in current directory")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()