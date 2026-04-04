"""
Tests for Grader
"""

import pytest
from bom_normalizer.grader import grade, _grade_easy, _grade_medium
from bom_normalizer.models import BOMRow, RowStatus


def test_grade_easy_perfect():
    """Test easy grading with perfect score"""
    rows = [
        BOMRow(row_id=1, vendor_name='Texas Instruments', part_number='SN74HC00N',
               value='5', package='DIP-14', quantity=10, status=RowStatus.NORMALIZED)
    ]
    gold = [
        BOMRow(row_id=1, vendor_name='Texas Instruments', part_number='SN74HC00N',
               value='5', package='DIP-14', quantity=10, status=RowStatus.NORMALIZED)
    ]
    
    score = _grade_easy(rows, gold)
    assert score == 1.0


def test_grade_easy_partial():
    """Test easy grading with partial score"""
    rows = [
        BOMRow(row_id=1, vendor_name='TI', part_number='SN74HC00N',
               value='5', package='DIP-14', quantity=10, status=RowStatus.RAW),
        BOMRow(row_id=2, vendor_name='Texas Instruments', part_number='GRM188R71H104KA93D',
               value='100e-9', package='0402', quantity=100, status=RowStatus.NORMALIZED)
    ]
    gold = [
        BOMRow(row_id=1, vendor_name='Texas Instruments', part_number='SN74HC00N',
               value='5', package='DIP-14', quantity=10, status=RowStatus.NORMALIZED),
        BOMRow(row_id=2, vendor_name='Texas Instruments', part_number='GRM188R71H104KA93D',
               value='100e-9', package='0402', quantity=100, status=RowStatus.NORMALIZED)
    ]
    
    score = _grade_easy(rows, gold)
    assert score == 0.5


def test_grade_medium():
    """Test medium grading"""
    rows = [
        BOMRow(row_id=1, vendor_name='Texas Instruments', part_number='SN74HC00N',
               value='5', package='DIP-14', quantity=10, status=RowStatus.NORMALIZED)
    ]
    gold = [
        BOMRow(row_id=1, vendor_name='Texas Instruments', part_number='SN74HC00N',
               value='5', package='DIP-14', quantity=10, status=RowStatus.NORMALIZED)
    ]
    
    score = _grade_medium(rows, gold)
    assert score == 1.0


def test_grade_dispatcher():
    """Test grade dispatcher"""
    rows = []
    gold = []
    
    score_easy = grade(rows, gold, 'easy')
    score_medium = grade(rows, gold, 'medium')
    score_hard = grade(rows, gold, 'hard')
    
    assert isinstance(score_easy, float)
    assert isinstance(score_medium, float)
    assert isinstance(score_hard, float)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
