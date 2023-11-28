from textwrap import dedent

import streamlit as st


def calculate_wacc(risk_free_rate, beta, market_risk_premium, cost_of_debt, tax_rate, total_debt, total_equity):
    """
    Calculates the Weighted Average Cost of Capital (WACC).

    :param risk_free_rate: The risk-free interest rate.
    :param beta: Beta of the company.
    :param market_risk_premium: Market risk premium.
    :param cost_of_debt: The cost of debt.
    :param tax_rate: Corporate tax rate.
    :param total_debt: Total debt of the company.
    :param total_equity: Total equity of the company / Total Shareholder Equity
    :return: WACC value.
    """
    cost_of_equity = risk_free_rate + beta * market_risk_premium
    equity_ratio = total_equity / (total_debt + total_equity)
    debt_ratio = total_debt / (total_debt + total_equity)

    return (cost_of_debt * debt_ratio * (1 - tax_rate)) + (cost_of_equity * equity_ratio)


def main():
    input_cols = iter(st.columns(4))

    with next(input_cols):
        risk_free_rate = st.number_input("Risk Free Rate")  # this returns a float
    with next(input_cols):
        beta = st.number_input("beta")
    with next(input_cols):
        market_risk_premium = st.number_input("market_risk_premium")
    with next(input_cols):
        cost_of_debt = st.number_input("cost_of_debt")

    # next row
    input_cols = iter(st.columns(4))

    with next(input_cols):
        tax_rate = st.number_input("tax_rate")
    with next(input_cols):
        total_debt = st.number_input("total_debt")
    with next(input_cols):
        total_equity = st.number_input("total_equity")

    output = f"""
    * risk_free_rate = {risk_free_rate}
    * beta = {beta}
    * market_risk_premium = {market_risk_premium}
    * cost_of_debt = {cost_of_debt}
    * tax_rate = {tax_rate}
    * total_debt = {total_debt}
    * total_equity = {total_equity}
    """
    output = dedent(output)
    st.write(output)
    st.divider()

    try:
        wacc = calculate_wacc(
            risk_free_rate, beta, market_risk_premium, cost_of_debt, tax_rate, total_debt, total_equity
        )
        st.write(wacc)
    except:  # put some real check here that we have valid data rather than just doing a try/except
        st.write("Input all data to compute wacc")


if __name__ == "__main__":
    main()
