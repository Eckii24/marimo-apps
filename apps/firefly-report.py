import marimo

__generated_with = "0.19.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd
    import io
    return alt, io, mo, pd


@app.cell
def _(mo):
    mo.md(r"""
    # Firefly Reporting

    ## Import Transaction CSV
    """)
    return


@app.cell
def _(mo):
    file = mo.ui.file(
        label="Select Transaction CSV",
        filetypes=[".csv"],
        kind="button",
    )

    file
    return (file,)


@app.cell
def _(file, io, mo, pd):
    mo.stop(len(file.value) == 0)

    try:
        csv_data = file.value[0].contents.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data), parse_dates=["date"])

    except Exception as e:
        print(f"Error reading CSV data: {e}")
        df = pd.DataFrame()
    return (df,)


@app.cell
def _(df, mo, pd):
    def get_column_values(column_name):
        _column_values = df[column_name].unique()
        _column_values = [
            value for value in _column_values if isinstance(value, str)
        ]
        _column_values.sort()

        return _column_values


    def get_column_selector(column_name, default_selector=None):
        _column_values = get_column_values(column_name)

        return mo.ui.multiselect(options=_column_values, value=default_selector)


    def get_column_selector_type(default_selector_type=None):
        return mo.ui.radio(options=["Include", "Exclude"], inline=True, value=default_selector_type)


    def get_column_array(column_name, default_selector_type=None, default_selector=None):
        return mo.ui.array(
            [
                get_column_selector_type(default_selector_type),
                get_column_selector(column_name, default_selector),
            ]
        )

    default_max_date = df["date"].max().date()
    default_min_date = (df["date"].max() - pd.DateOffset(years=1)).date()

    filters = mo.ui.dictionary(
        {
            "date": mo.ui.array([mo.ui.date_range(
                start=df["date"].min().date(),
                stop=df["date"].max().date(),
                value=(default_min_date, default_max_date)
            )]),
            "amount": mo.ui.array([mo.ui.range_slider(
                start=df["amount"].min(),
                stop=df["amount"].max(),
                show_value=True,
            )]),
            "category": get_column_array("category"),
            "tags": get_column_array("tags"),
            "type": get_column_array("type", default_selector_type="Include", default_selector=["Deposit", "Withdrawal"]),
            "source_name": get_column_array("source_name"),
            "source_type": get_column_array("source_type"),
            "destination_name": get_column_array("destination_name"),
            "destination_type": get_column_array("destination_type"),
        }
    )
    return (filters,)


@app.cell
def _(df, filters, mo):
    displays = mo.ui.dictionary(
        {
            "date_aggregation": mo.ui.radio(
                options=["Day", "Week", "Month", "Quarter", "Year"], inline=True, value="Month"
            ),
            "group_by": mo.ui.dropdown(
                options=list(filters.value.keys()), value="category"
            ),
            "columns": mo.ui.multiselect(
                options=list(df.columns),
                value=["date", "type", "amount", "description", "source_name", "source_type", "destination_name", "destination_type", "category", "tags", "budget", "bill"],
            )
        }
    )
    return (displays,)


@app.cell
def _(file, mo):
    mo.stop(len(file.value) == 0)
    mo.md("## Data operations")
    return


@app.cell
def _(displays, filters, mo):
    mo.accordion(
        {
            "Filter": mo.vstack(
                [
                    *[
                        mo.hstack(
                            [mo.md(selector), *items],
                            justify="start",
                            gap=5,
                            widths=[1, 1, 4],
                        )
                        for selector, items in filters.items()
                    ]
                ]
            ),
            "Display": mo.vstack(
                [
                    *[
                        mo.hstack(
                            [mo.md(selector), items],
                            justify="start",
                            gap=5,
                            widths=[1, 4],
                        )
                        for selector, items in displays.items()
                    ]
                ]
            ),
        }
    )
    return


@app.cell
def _(file, mo):
    mo.stop(len(file.value) == 0)
    mo.md("## Data Analysis")
    return


@app.cell
def _(df, filters, pd):
    df_filtered = df.copy()

    # Date Range Filter
    df_filtered = df_filtered[
        (df_filtered["date"] >= pd.Timestamp(filters["date"][0].value[0], tz="Europe/Berlin"))
        & (df_filtered["date"] <= pd.Timestamp(filters["date"][0].value[1], tz="Europe/Berlin"))
    ]

    # Amount Range Filter
    df_filtered = df_filtered[
        (df_filtered["amount"] >= filters["amount"][0].value[0])
        & (df_filtered["amount"] <= filters["amount"][0].value[1])
    ]


    def apply_filter(_df, column_name):
        selector_array = filters[column_name]
        selector_type = selector_array[0].value
        selector_values = selector_array[1].value

        if selector_type is None or not selector_values:
            return _df

        if selector_type == "Include":
            _df = _df[_df[column_name].isin(selector_values)]
        elif selector_type == "Exclude":
            _df = _df[~_df[column_name].isin(selector_values)]
        return _df


    # Category Filter
    df_filtered = apply_filter(df_filtered, "category")
    df_filtered = apply_filter(df_filtered, "tags")
    df_filtered = apply_filter(df_filtered, "type")
    df_filtered = apply_filter(df_filtered, "source_name")
    df_filtered = apply_filter(df_filtered, "source_type")
    df_filtered = apply_filter(df_filtered, "destination_name")
    df_filtered = apply_filter(df_filtered, "destination_type")
    return (df_filtered,)


@app.cell
def _(df_filtered, displays, pd):
    df_displayed = df_filtered.copy()

    # Date Aggregation
    timezone = 'Europe/Berlin'
    date_aggregation_value = displays["date_aggregation"].value

    if date_aggregation_value == "Day":
        df_displayed["date_aggregation"] = pd.to_datetime(df_displayed["date"], utc=True).dt.tz_convert(timezone).dt.strftime('%Y-%m-%d')
    elif date_aggregation_value == "Week":
        df_displayed["date_aggregation"] = pd.to_datetime(df_displayed["date"], utc=True).dt.tz_convert(timezone).dt.strftime('%Y-W%U')
    elif date_aggregation_value == "Month":
        df_displayed["date_aggregation"] = pd.to_datetime(df_displayed["date"], utc=True).dt.tz_convert(timezone).dt.strftime('%Y-%m')
    elif date_aggregation_value == "Quarter":
        df_displayed["date_aggregation"] = pd.to_datetime(df_displayed["date"], utc=True).dt.tz_convert(timezone).dt.strftime('%Y-Q%q')
    elif date_aggregation_value == "Year":
        df_displayed["date_aggregation"] = pd.to_datetime(df_displayed["date"], utc=True).dt.tz_convert(timezone).dt.strftime('%Y')
    else:
        df_displayed["date_aggregation"] = pd.to_datetime(df_displayed["date"], utc=True).dt.tz_convert(timezone).dt.strftime('%Y-%m-%d')

    # Group By
    group_by = displays["group_by"].value if displays["group_by"].value else None

    if group_by:
        df_grouped = df_displayed.pivot_table(
            index=group_by,
            columns="date_aggregation",
            values="amount",
            aggfunc="sum",
            fill_value=0
        )
        df_grouped = df_grouped.reset_index()
    else:
        df_grouped = df_displayed.groupby("date_aggregation")["amount"].sum().reset_index()

    average = df_grouped.mean(numeric_only=True, axis=1)
    df_grouped['Total'] = df_grouped.sum(numeric_only=True, axis=1)

    df_grouped['Average'] = average

    df_grouped = df_grouped.sort_values(by='Total', ascending=True)
    df_grouped.loc['Total']= df_grouped.sum(numeric_only=True, axis=0)
    return df_displayed, df_grouped, group_by


@app.cell
def _(df_grouped, group_by, mo):
    def style_cell(row_id, column_name, value):
        if isinstance(value, (int, float)) and value < 0:
            return {"color": "red"}
        elif isinstance(value, (int, float)) and value > 0:
            return {"color": "green"}
        else:
            return {}


    selection = mo.ui.table(
        df_grouped,
        selection="single-cell",
        page_size=25,
        style_cell=style_cell,
        format_mapping={
            col: lambda x: "{:,.2f}".format(x)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
            for col in df_grouped.columns
            if col not in group_by
        },
        freeze_columns_left=[df_grouped.columns[0]],
    )
    selection
    return selection, style_cell


@app.cell
def _(alt, df_grouped, displays, mo, selection):
    if (
        not selection.value
        or not displays["group_by"].value
        or not selection.value[0].column == displays["group_by"].value
    ):
        mo.stop("No selection made.")

    group_by_column = displays["group_by"].value
    selected_value = df_grouped[group_by_column].iloc[int(selection.value[0].row)]

    diagram_data = df_grouped[df_grouped[group_by_column] == selected_value]

    # Melt the dataframe for easier plotting
    _diagram_data = diagram_data.melt(
        id_vars=[group_by_column],
        value_vars=[
            col
            for col in diagram_data.columns
            if col not in [group_by_column, "Total", "Average"]
        ],
        var_name="date_aggregation",
        value_name="amount",
    )

    # Create the chart
    chart = mo.ui.altair_chart(
        alt.Chart(_diagram_data)
        .mark_bar()
        .encode(
            x=alt.X("date_aggregation:N", title="Date Aggregation"),
            y=alt.Y("amount:Q", title="Amount"),
            tooltip=[group_by_column, "date_aggregation", "amount"],
        )
        .properties(title=f"Amount for {group_by_column} = {selected_value}")
    )
    chart
    return (chart,)


@app.cell
def _(df_displayed, df_grouped, displays, mo, selection, style_cell):
    if (
        not selection.value
        or selection.value[0].column == displays["group_by"].value
    ):
        mo.stop("No selection made.")

    row_index = int(selection.value[0].row)
    column_name = selection.value[0].column

    if displays["group_by"].value:
        row_name = df_grouped[displays["group_by"].value].iloc[row_index]

        df_selected = df_displayed[
            (
                df_grouped.index[int(selection.value[0].row)] == "Total"
                or df_displayed[displays["group_by"].value] == row_name
            )
            & (
                column_name == "Total"
                or column_name == "Average"
                or df_displayed["date_aggregation"] == column_name
            )
        ]
    else:
        row_name = df_grouped["date_aggregation"].iloc[row_index]

        df_selected = df_displayed[
            column_name == "Total"
            or column_name == "Average"
            or df_displayed["date_aggregation"] == column_name
        ]

    df_selected = df_selected[displays["columns"].value]

    mo.ui.table(
        df_selected,
        page_size=25,
        format_mapping={
            "amount": lambda x: "{:,.2f}".format(x)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
            "date": lambda x: x.strftime("%Y-%m-%d"),
        },
        style_cell=style_cell,
    )
    return


@app.cell
def _(chart, df_displayed, df_grouped, displays, mo, selection, style_cell):
    if not len(chart.value["date_aggregation"].values):
        mo.stop("No selection made.")

    _row_index = int(selection.value[0].row)
    _column_names = chart.value["date_aggregation"].values

    _row_name = df_grouped[displays["group_by"].value].iloc[_row_index]

    _df_selected = df_displayed[
        (df_displayed[displays["group_by"].value] == _row_name)
        & (df_displayed["date_aggregation"].isin(_column_names))
    ]

    _df_selected = _df_selected[displays["columns"].value]

    mo.ui.table(
        _df_selected,
        page_size=25,
        format_mapping={
            "amount": lambda x: "{:,.2f}".format(x)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
            "date": lambda x: x.strftime("%Y-%m-%d"),
        },
        style_cell=style_cell,
    )
    return


if __name__ == "__main__":
    app.run()
