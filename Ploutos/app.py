import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

app = dash.Dash()

df = pd.read_csv(
    "https://raw.githubusercontent.com/ThuwarakeshM/geting-started-with-plottly-dash/main/life_expectancy.csv"
)

fig = px.scatter(
    df,
    x="GDP",
    y="Life expectancy",
    size="Population",
    color="continent",
    hover_name="Country",
    log_x=True,
    size_max=60,
)

app.layout = html.Div([dcc.Graph(id="life-exp-vs-gdp", figure=fig)])


if __name__ == "__main__":
    app.run_server(debug=True)