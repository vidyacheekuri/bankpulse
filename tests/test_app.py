from pathlib import Path
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
