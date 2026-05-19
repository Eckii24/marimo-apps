import marimo

__generated_with = "0.19.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    csv_file = mo.ui.file(label="Upload CSV file")
    csv_file
    return csv_file, mo, pd


@app.cell
def _(csv_file, mo, pd):
    import io

    if csv_file.value:
        df_uploaded_csv = pd.read_csv(io.BytesIO(csv_file.value[0].contents), sep=';', on_bad_lines='skip')
    else:
        mo.md("Upload a CSV file to view its content.")
    return (df_uploaded_csv,)


@app.cell
def _(df_uploaded_csv):
    df_filtered = df_uploaded_csv[df_uploaded_csv["type"].ne("trainer")]
    df_grouped = df_filtered.groupby(['year', 'day', 'time', 'name']).size().reset_index(name='count')
    df_pivot = df_grouped.pivot_table(index='name', columns=['year', 'day', 'time'], values='count', fill_value=0)
    return (df_pivot,)


@app.cell
def _(df_pivot, mo):
    column_selector = mo.ui.multiselect(
        value=[col for col in df_pivot.columns if col[0] == 2023],
        options=list(df_pivot.columns),
        label="Select columns to display"
    )

    column_selector
    return (column_selector,)


@app.cell
def _(column_selector, df_pivot):
    selected_columns = column_selector.value
    df_selected = df_pivot[selected_columns].copy()
    df_selected['Total Sum'] = df_selected.sum(axis=1)
    df_selected
    return


if __name__ == "__main__":
    app.run()
