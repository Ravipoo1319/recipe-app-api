from django.test import SimpleTestCase
from app import calc

class CalcTest(SimpleTestCase):
    """Test calss to test the calc module."""
    
    def test_add_function(self):
        """Test the add function."""
        res = calc.add(10,15)
        self.assertEqual(res,25)
        
    def test_substract_function(self):
        """Test the substract function."""
        res = calc.substract(10,15)
        self.assertEqual(res,5)