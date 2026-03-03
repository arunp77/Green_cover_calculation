"""
Unit tests for Green Cover Calculator
"""

import sys
from pathlib import Path
import numpy as np
import unittest
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from ndvi_calculator import NDVICalculator, GreenCoverAnalyzer

# # Add src to path
# sys.path.insert(0, str(Path(__file__).parent / 'src'))

# from ndvi_calculator import NDVICalculator, GreenCoverAnalyzer
from data_loader import SatelliteDataLoader
from visualization import VegetationVisualizer


class TestNDVICalculator(unittest.TestCase):
    """Test NDVI calculation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.red = np.array([[100, 120], [110, 130]])
        self.nir = np.array([[150, 200], [160, 210]])
        self.calc = NDVICalculator(self.red, self.nir)
    
    def test_ndvi_range(self):
        """Test that NDVI values are in [-1, 1] range"""
        ndvi = self.calc.calculate_ndvi()
        valid_ndvi = ndvi[~np.isnan(ndvi)]
        self.assertTrue(np.all(valid_ndvi >= -1))
        self.assertTrue(np.all(valid_ndvi <= 1))
    
    def test_ndvi_shape(self):
        """Test that NDVI has correct shape"""
        ndvi = self.calc.calculate_ndvi()
        self.assertEqual(ndvi.shape, self.red.shape)
    
    def test_green_cover_percentage(self):
        """Test green cover calculation"""
        self.calc.calculate_ndvi()
        green_cover, mask = self.calc.calculate_green_cover(ndvi_threshold=0.2)
        self.assertIsInstance(green_cover, float)
        self.assertGreaterEqual(green_cover, 0)
        self.assertLessEqual(green_cover, 100)
    
    def test_ndvi_statistics(self):
        """Test NDVI statistics calculation"""
        self.calc.calculate_ndvi()
        stats = self.calc.get_ndvi_statistics()
        
        self.assertIn('mean', stats)
        self.assertIn('std', stats)
        self.assertIn('min', stats)
        self.assertIn('max', stats)
        self.assertGreaterEqual(stats['max'], stats['min'])


class TestGreenCoverAnalyzer(unittest.TestCase):
    """Test vegetation classification"""
    
    def setUp(self):
        """Set up test NDVI data"""
        self.ndvi = np.array([
            [-0.5, 0.1, 0.3, 0.5, 0.8],
            [0.0, 0.2, 0.4, 0.6, 0.9],
            [0.15, 0.35, 0.55, 0.75, 1.0]
        ])
        self.analyzer = GreenCoverAnalyzer(self.ndvi)
    
    def test_vegetation_classification(self):
        """Test vegetation classification"""
        classification, percentages = self.analyzer.classify_vegetation()
        
        # Check that all classes are present or percentages sum to 100
        total_percentage = sum(percentages.values())
        self.assertAlmostEqual(total_percentage, 100.0, places=1)
    
    def test_green_area_stats(self):
        """Test area statistics calculation"""
        stats = self.analyzer.get_green_area_stats(pixel_size=30.0)
        
        self.assertIn('total_area_km2', stats)
        self.assertIn('green_area_km2', stats)
        self.assertIn('green_cover_percentage', stats)
        self.assertGreaterEqual(stats['green_area_km2'], 0)
        self.assertGreaterEqual(stats['total_area_km2'], stats['green_area_km2'])


class TestDataLoader(unittest.TestCase):
    """Test data loading functionality"""
    
    def setUp(self):
        """Set up loader"""
        self.loader = SatelliteDataLoader()
    
    def test_synthetic_data_generation(self):
        """Test synthetic data generation"""
        bands = self.loader.create_synthetic_data(height=50, width=50, seed=42)
        
        self.assertIn('red', bands)
        self.assertIn('nir', bands)
        self.assertIn('blue', bands)
        
        self.assertEqual(bands['red'].shape, (50, 50))
        self.assertEqual(bands['nir'].shape, (50, 50))
        self.assertEqual(bands['blue'].shape, (50, 50))
    
    def test_data_range(self):
        """Test that synthetic data is in valid range"""
        bands = self.loader.create_synthetic_data()
        
        for band_name, band_data in bands.items():
            self.assertGreaterEqual(np.min(band_data), 0)
            self.assertLessEqual(np.max(band_data), 255)


class TestVisualization(unittest.TestCase):
    """Test visualization functionality"""
    
    def setUp(self):
        """Set up visualizer"""
        self.visualizer = VegetationVisualizer(output_directory="output/tests")
        self.test_array = np.random.rand(10, 10)
    
    def test_normalize_band(self):
        """Test band normalization"""
        band = np.array([[0, 50], [100, 200]])
        normalized = VegetationVisualizer._normalize_band(band)
        
        self.assertLessEqual(np.max(normalized), 1.0)
        self.assertGreaterEqual(np.min(normalized), 0.0)
    
    def test_visualization_output(self):
        """Test that visualization creates output"""
        # This test checks if the matplotlib functions don't crash
        if self.visualizer.matplotlib_available:
            path = self.visualizer.plot_ndvi(self.test_array, 
                                            output_filename="test_ndvi.png")
            # Should return a path or None
            self.assertTrue(path is None or isinstance(path, str))


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete analysis workflow"""
        # Generate data
        loader = SatelliteDataLoader()
        bands = loader.create_synthetic_data(height=50, width=50)
        
        # Calculate NDVI
        calc = NDVICalculator(bands['red'], bands['nir'])
        ndvi = calc.calculate_ndvi()
        
        # Get statistics
        stats = calc.get_ndvi_statistics()
        self.assertGreater(stats['valid_pixels'], 0)
        
        # Calculate green cover
        green_cover, _ = calc.calculate_green_cover()
        self.assertGreaterEqual(green_cover, 0)
        self.assertLessEqual(green_cover, 100)
        
        # Classify vegetation
        analyzer = GreenCoverAnalyzer(ndvi)
        classification, percentages = analyzer.classify_vegetation()
        self.assertEqual(classification.shape, ndvi.shape)
        
        # Get area stats
        area_stats = analyzer.get_green_area_stats()
        self.assertGreater(area_stats['total_area_km2'], 0)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()


