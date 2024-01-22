import streamlit as st

SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "SANDBOX.BI_TEAM")
QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.SALES_MATERIAL_NO_COUNTRY_BY_MONTH_TIME_SERIES"
TABLE_DESCRIPTION = """
One table has various metrics for financial entities (also referred to as banks) since 2020.
The user may describe the entities interchangeably as banks, financial institutions, or financial entities.
The other table has various metrics for product ratings on Amazon ecommerce website.
The user may describe the ratings as traffic.
"""
# This query is optional if running Edgie on your own table, especially a wide table.
# Since this is a deep table, it's useful to tell Edgie what variables are available.
# Similarly, if you have a table with semi-structured data (like JSON), it could be used to provide hints on available keys.
# If altering, you may also need to modify the formatting logic in get_table_context() below.


METADATA_QUERY = (
    f"SELECT VARIABLE_NAME, DEFINITION FROM {SCHEMA_PATH}.SALES_MATERIAL_NO_COUNTRY_BY_MONTH_TIME_SERIES;"
)

GEN_SQL = """
You will be acting as an AI Snowflake SQL Expert named Edgie, an AI Chatbot..
Your goal is to give correct, executable sql query to users.
You will be replying to users who will be confused if you don't respond in the character of Frosty.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table.

Here are some example user questions along with the expected SQL queries:

- **User Question:** What is the net sales in US dollars?
**Expected SQL Query:**
```sql
SELECT SUM(VALUE) as AGGREGATED_VALUE
FROM {{{{QUALIFIED_TABLE_NAME}}}}
WHERE DEFINITION = 'Net sales represent the revenue from all sales...'
AND UNIT = 'USD'


- **User Question:** What is the net sales?
**Expected SQL Query:**
```sql
    SELECT UNIT, SUM(VALUE) as AGGREGATED_VALUE
    FROM {{{{QUALIFIED_TABLE_NAME}}}}
    WHERE DEFINITION = 'Net sales represent the revenue from all sales...'
    GROUP BY UNIT

- **User Question:** What is the gross profit?
**Expected SQL Query:**
```sql
    SELECT UNIT, SUM(VALUE) as AGGREGATED_VALUE
    FROM {{{{QUALIFIED_TABLE_NAME}}}}
    WHERE DEFINITION = 'Gross profit is a metric for the total profits...'
    GROUP BY UNIT

{context}

The United States is known in the data as USA.

Here are 6 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. Unless otherwise specified, limit the number of responses in the SQL query to 10. However, if there is a need for ordering numbers, the response limit may extend beyond 10 to accommodate the ordered sequence.
3. Text/string WHERE clauses must use fuzzy matching (e.g., ilike %keyword%).
4. Generate a single Snowflake SQL code, do not create multiple ones.
5. Use only the table columns provided in <columns> and the table provided in <tableName>. Do not make assumptions or hallucinations about the table names.
6. Do not place numerical values at the beginning of SQL variables. Instead, place them after the variable name or as a value in a condition.
7. When the user asks for a general metric such as net sales or gross profit without specifying a currency, provide the aggregates for each currency by including `UNIT` in the `GROUP BY` clause of the SQL query.
8. Always order the results in the SQL query using the ORDER BY clause. If no specific order is specified, order by the first selected column in ascending order.
9. When joining tables, make sure the tables are related and have a common column. Use this common column in the ON clause of the JOIN statement.
10. Always include relevant columns in the SELECT statement to provide context for the data. If the question involves a specific attribute like 'year' or 'country', ensure these are selected in the SQL query.
11. When currency information is needed, join the data with the "DATAWAREHOUSE.ENTERPRISE.HYPERION_EXCHANGE_RATES" table to provide the relevant currency details.
</rules>
Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response.

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""

@st.cache_data(show_spinner="Loading Edgie's context...")
def get_table_context(table_names: list, metadata_query: str = None):
    table_contexts = []
    for table_name in table_names:
        table = table_name.split(".")
        conn = st.connection("snowflake")
        columns = conn.query(f"""
            SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
            """, show_spinner=False,
        )
        columns = "\n".join(
            [
                f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
                for i in range(len(columns["COLUMN_NAME"]))
            ]
        )
        context = f"""
    Here is the table name <tableName> {'.'.join(table)} </tableName>

    Here are the columns of the {'.'.join(table)}

    <columns>\n\n{columns}\n\n</columns>
        """
        if metadata_query:
            metadata = conn.query(metadata_query, show_spinner=False)
            metadata = "\n".join(
                [
                    f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                    for i in range(len(metadata["VARIABLE_NAME"]))
                ]
            )
            context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
        table_contexts.append(context)
    return table_contexts


def get_system_prompt():
    table_names = ['SANDBOX.BI_TEAM.SALES_MATERIAL_NO_COUNTRY_BY_MONTH_TIME_SERIES', 'SANDBOX.BI_TEAM.ATLAS_TRAFFIC_PRODUCTS_AND_KEYWORDS_BY_MONTH_TIME_SERIES']
    table_contexts = get_table_context(
        table_names=table_names,
        metadata_query=METADATA_QUERY
    )
    # Join all table contexts with a separator
    all_table_contexts = "\n---\n".join(table_contexts)
    for table_context in table_contexts:
        st.write(table_context)
    return GEN_SQL.format(context=all_table_contexts)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for Edgie")
    st.markdown(get_system_prompt())
