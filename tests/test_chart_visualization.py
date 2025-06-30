"""
Chart visualization tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.tool.chart_visualization.data_visualization import (
    ChartType,
    DataPreprocessor,
    DataVisualization,
)


@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return pd.DataFrame(
        {
            "x": range(10),
            "y": [i * 2 for i in range(10)],
            "category": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
        }
    )


@pytest.fixture
def data_visualizer():
    """Create data visualizer instance"""
    return DataVisualization()


def test_chart_type_enum():
    """Test chart type enumeration"""
    assert ChartType.LINE in ChartType
    assert ChartType.BAR in ChartType
    assert ChartType.SCATTER in ChartType
    assert ChartType.PIE in ChartType
    assert ChartType.HEATMAP in ChartType


def test_data_preprocessor():
    """Test data preprocessing"""
    preprocessor = DataPreprocessor()
    data = pd.DataFrame({"x": [1, 2, None, 4, 5], "y": [10, None, 30, 40, 50]})

    processed = preprocessor.preprocess(data)
    assert processed.isnull().sum().sum() == 0  # No null values
    assert len(processed) == 3  # Rows with null values removed


def test_line_chart(data_visualizer, sample_data):
    """Test line chart creation"""
    chart = data_visualizer.create_line_chart(
        data=sample_data, x="x", y="y", title="Test Line Chart"
    )
    assert chart is not None
    assert "Test Line Chart" in chart
    assert "line" in chart.lower()


def test_bar_chart(data_visualizer, sample_data):
    """Test bar chart creation"""
    chart = data_visualizer.create_bar_chart(
        data=sample_data, x="category", y="y", title="Test Bar Chart"
    )
    assert chart is not None
    assert "Test Bar Chart" in chart
    assert "bar" in chart.lower()


def test_scatter_plot(data_visualizer, sample_data):
    """Test scatter plot creation"""
    chart = data_visualizer.create_scatter_plot(
        data=sample_data, x="x", y="y", title="Test Scatter Plot"
    )
    assert chart is not None
    assert "Test Scatter Plot" in chart
    assert "scatter" in chart.lower()


def test_pie_chart(data_visualizer, sample_data):
    """Test pie chart creation"""
    value_counts = sample_data["category"].value_counts()
    chart = data_visualizer.create_pie_chart(data=value_counts, title="Test Pie Chart")
    assert chart is not None
    assert "Test Pie Chart" in chart
    assert "pie" in chart.lower()


def test_heatmap(data_visualizer):
    """Test heatmap creation"""
    data = np.random.rand(5, 5)
    chart = data_visualizer.create_heatmap(data=data, title="Test Heatmap")
    assert chart is not None
    assert "Test Heatmap" in chart
    assert "heatmap" in chart.lower()


def test_invalid_data():
    """Test handling of invalid data"""
    visualizer = DataVisualization()

    with pytest.raises(ValueError):
        visualizer.create_line_chart(data=None, x="x", y="y", title="Invalid Chart")


def test_missing_columns(data_visualizer, sample_data):
    """Test handling of missing columns"""
    with pytest.raises(ValueError):
        data_visualizer.create_line_chart(
            data=sample_data, x="nonexistent", y="y", title="Invalid Chart"
        )


def test_chart_customization(data_visualizer, sample_data):
    """Test chart customization options"""
    chart = data_visualizer.create_line_chart(
        data=sample_data,
        x="x",
        y="y",
        title="Custom Chart",
        width=800,
        height=600,
        color="red",
    )
    assert chart is not None
    assert "width: 800" in chart
    assert "height: 600" in chart
    assert "red" in chart


def test_multiple_series(data_visualizer, sample_data):
    """Test multiple series in one chart"""
    chart = data_visualizer.create_line_chart(
        data=sample_data, x="x", y=["y", "y"], title="Multiple Series"
    )
    assert chart is not None
    assert "Multiple Series" in chart
    assert chart.count("line") > 1  # Multiple lines


def test_data_transformation(data_visualizer, sample_data):
    """Test data transformation before visualization"""
    transformed_data = data_visualizer.transform_data(
        data=sample_data, aggregation="mean", group_by="category"
    )
    assert isinstance(transformed_data, pd.DataFrame)
    assert len(transformed_data) == 2  # Two categories


def test_chart_export(data_visualizer, sample_data):
    """Test chart export functionality"""
    with patch(
        "app.tool.chart_visualization.data_visualization.save_chart"
    ) as mock_save:
        chart = data_visualizer.create_line_chart(
            data=sample_data, x="x", y="y", title="Export Test"
        )
        data_visualizer.export_chart(chart, "test.html")
        mock_save.assert_called_once()
