import uuid
from unittest.mock import MagicMock, patch

from tools.generate_chart import ChartSeries, generate_chart


def _series(*values: float, name: str = "Value") -> ChartSeries:
    return ChartSeries(name=name, values=list(values))


@patch("tools.generate_chart.ensure_bucket")
@patch("tools.generate_chart.get_client")
async def test_bar_chart_uploads_and_returns_chart_id(mock_get_client, mock_ensure_bucket):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    result = await generate_chart(
        title="Ad Revenue by Quarter",
        chart_type="bar",
        labels=["Q1", "Q2"],
        series=[_series(10, 20)],
    )

    assert "chart_id" in result
    uuid.UUID(result["chart_id"])  # a real, parseable UUID
    assert result["title"] == "Ad Revenue by Quarter"
    assert result["chart_type"] == "bar"
    mock_ensure_bucket.assert_called_once_with(mock_client, "nova-charts")
    assert mock_client.put_object.call_args.args[0] == "nova-charts"
    assert mock_client.put_object.call_args.kwargs["content_type"] == "image/png"


@patch("tools.generate_chart.ensure_bucket")
@patch("tools.generate_chart.get_client")
async def test_line_chart_multi_series(mock_get_client, mock_ensure_bucket):
    mock_get_client.return_value = MagicMock()

    result = await generate_chart(
        title="Rating Trend",
        chart_type="line",
        labels=["Jan", "Feb", "Mar"],
        series=[_series(1, 2, 3, name="Adults 18-49"), _series(2, 3, 4, name="Adults 25-54")],
    )

    assert "chart_id" in result


@patch("tools.generate_chart.ensure_bucket")
@patch("tools.generate_chart.get_client")
async def test_pie_chart_single_series(mock_get_client, mock_ensure_bucket):
    mock_get_client.return_value = MagicMock()

    result = await generate_chart(
        title="Revenue Share",
        chart_type="pie",
        labels=["TV", "Plus", "News"],
        series=[_series(50, 30, 20)],
    )

    assert "chart_id" in result


async def test_pie_chart_rejects_multiple_series():
    result = await generate_chart(
        title="Bad Pie",
        chart_type="pie",
        labels=["A", "B"],
        series=[_series(1, 2), _series(3, 4)],
    )
    assert "error" in result


async def test_rejects_mismatched_labels_and_values_length():
    result = await generate_chart(
        title="Bad Lengths",
        chart_type="bar",
        labels=["A", "B", "C"],
        series=[_series(1, 2)],
    )
    assert "error" in result


async def test_rejects_empty_series():
    result = await generate_chart(title="No Series", chart_type="bar", labels=["A"], series=[])
    assert "error" in result


async def test_rejects_unsupported_chart_type():
    result = await generate_chart(
        title="Bad Type",
        chart_type="scatter",  # type: ignore[arg-type]
        labels=["A", "B"],
        series=[_series(1, 2)],
    )
    assert "error" in result
