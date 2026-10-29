from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
def test_workspaces_filters_and_zero_capacity():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run();assert not app.exception
    app.multiselect[0].set_value([]).run();assert not app.exception
    assert app.metric[0].value=='0' and app.metric[1].value=='n.a.'
    for page in ['Issue explorer','Response quality','Review planning','Project evidence']:
        app.sidebar.radio[0].set_value(page).run();assert not app.exception,page
        if page=='Review planning':
            app.number_input[0].set_value(0).run();assert not app.exception
            assert app.metric[1].value=='0'


@pytest.mark.parametrize('page', ['Issue explorer', 'Review planning'])
@pytest.mark.parametrize('product', ['Credit card', 'Checking or savings account'])
def test_product_selection_reconciles_to_source(page, product):
    source = pd.read_parquet(ROOT / 'data/processed/complaints.parquet')
    complete = source.loc[source.is_complete_month]
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    app.sidebar.radio[0].set_value(page).run()
    next(widget for widget in app.selectbox if widget.label == 'Product').set_value(product).run()
    assert not app.exception
    selected = complete.loc[complete['product'].eq(product)]
    if page == 'Issue explorer':
        baseline = next(widget.value for widget in app.selectbox if widget.label == 'Baseline month')
        comparison = next(widget.value for widget in app.selectbox if widget.label == 'Comparison month')
        expected = [selected.month.eq(baseline).sum(), selected.month.eq(comparison).sum()]
        assert [metric.value for metric in app.metric[:2]] == [f'{value:,}' for value in expected]
    else:
        month = next(widget.value for widget in app.selectbox if widget.label == 'Review month')
        expected = (selected.month.eq(month) & selected.timely.eq('No')).sum()
        assert app.metric[0].value == f'{expected:,}'
