import numpy as np
import pandas as pd
import math
from pprint import pprint

def data_quality(df):

    temp = df.copy()

    #Correct datatypes
    cols_to_convert = [
    'income',
    'num_mortgages',
    'num_credit_lines',
    'num_cancellations_12m',
    'num_derogatory_marks',
    'months_since_last_delinquency',
    'principal'
    ]
    
    #Round values
    for col in cols_to_convert:
        temp[col] = temp[col].round(0)
    
    #Convert to Int64 (nullable, admits NaNs)
    temp = temp.astype({col: 'Int64' for col in cols_to_convert})

    #Impute value categorical
    value = 'Unknown'    
    for column in temp.select_dtypes(exclude = 'number').columns:
        temp[column] = temp[column].fillna(value)

    #Impute value numerical
    for column in temp.select_dtypes(include='number').columns:
        temp[column] = temp[column].fillna(0)

    #Group categories
    temp.housing = temp.housing.replace(['ANY','OTHER','NONE'],'MORTGAGE')
    temp.purpose = temp.purpose.replace(['wedding','renewable_energy','educational'],'others')
    
    return(temp)

def annuity_payment(P, r, n):
    """Cuota mensual constante (sistema francés). r = tasa mensual (decimal)."""
    if abs(r) < 1e-15:
        return P / n
    return P * (r * (1 + r)**n) / ((1 + r)**n - 1)

def find_rate_bisection(func, low=0.0, high=1.0, max_attempts=80, tol=1e-12):
    """Bisección con expansión de 'high' si no cambia signo. Devuelve None si no encuentra raíz."""
    f_low = func(low)
    if abs(f_low) < tol:
        return low
    f_high = func(high)
    attempts = 0
    while f_low * f_high > 0 and attempts < max_attempts:
        high *= 2.0
        f_high = func(high)
        attempts += 1
    if f_low * f_high > 0:
        return None
    for _ in range(200):
        mid = 0.5 * (low + high)
        f_mid = func(mid)
        if abs(f_mid) < tol:
            return mid
        if f_mid * f_low > 0:
            low, f_low = mid, f_mid
        else:
            high = mid
    return mid

def price_rate_and_payment(principal, n_months,
                           EL_rate=None, EL_total=None,
                           euribor_annual=0.02,
                           K_pct=0.08, r_capital=0.10, capital_amount=None,
                           op_cost_rate=None, op_cost_amount=None,
                           margin_rate=None, margin_amount=None,
                           use_funding_as_discount=True,
                           verbose=False):
    """
    Calcula tasa mensual (y EAR) y cuota mensual para cubrir:
      - Expected Loss (EL) (puede pasar EL_rate o EL_total)
      - Coste de capital (K_pct * saldo * r_capital) o capital_amount absoluto
      - Costes operativos (op_cost_rate anual sobre saldo o op_cost_amount absoluto)
      - Margen objetivo (margin_rate anual sobre saldo o margin_amount absoluto)

    euribor_annual se usa como tasa de descuento/funding por defecto.
    Devuelve: dict(monthly_rate, EAR, monthly_payment, amortization_table)
    """

    # Validaciones
    if EL_total is None:
        if EL_rate is None:
            raise ValueError("Debes pasar EL_rate o EL_total")
        EL_total = EL_rate * principal

    # tasa de descuento mensual (para descontar flujos) desde euribor anual
    funding_monthly = (1 + euribor_annual) ** (1/12) - 1 if use_funding_as_discount else 0.0

    def npv_for_monthly_rate(r):
        # cuota con tasa r
        A = annuity_payment(principal, r, n_months)

        # saldos al inicio de cada periodo
        start_balances = []
        bal = principal
        for _ in range(n_months):
            start_balances.append(bal)
            interest = bal * r
            principal_repay = A - interest
            bal = max(bal - principal_repay, 0.0)
        total_bal = sum(start_balances) or 1.0

        # EL mensual asignado proporcionalmente al saldo vivo
        EL_monthly = [EL_total * (b / total_bal) for b in start_balances]

        # coste de capital mensual (por saldo)
        if capital_amount is None:
            capital_monthly = [b * (K_pct * r_capital / 12.0) for b in start_balances]
        else:
            # si pasas capital_amount como absoluto, repartir proporcionalmente
            capital_monthly = [capital_amount * (b / total_bal) for b in start_balances]

        # costes operativos
        if op_cost_amount is not None:
            op_monthly = [op_cost_amount * (b / total_bal) for b in start_balances]
        elif op_cost_rate is not None:
            op_monthly = [b * (op_cost_rate / 12.0) for b in start_balances]
        else:
            op_monthly = [0.0] * n_months

        # margen
        if margin_amount is not None:
            margin_monthly = [margin_amount * (b / total_bal) for b in start_balances]
        elif margin_rate is not None:
            margin_monthly = [b * (margin_rate / 12.0) for b in start_balances]
        else:
            margin_monthly = [0.0] * n_months

        # NPV = -principal (desembolso) + suma de flujos esperados descontados
        npv = -principal
        for t in range(n_months):
            net = A - EL_monthly[t] - capital_monthly[t] - op_monthly[t] - margin_monthly[t]
            if funding_monthly:
                npv += net / ((1 + funding_monthly) ** (t + 1))
            else:
                npv += net
        return npv

    # si con r=0 ya cubre todo, no se necesita tasa
    if npv_for_monthly_rate(0.0) >= 0:
        monthly_rate = 0.0
    else:
        monthly_rate = find_rate_bisection(npv_for_monthly_rate, low=0.0, high=0.5, max_attempts=100, tol=1e-12)
        if monthly_rate is None:
            monthly_rate = find_rate_bisection(npv_for_monthly_rate, low=0.0, high=5.0, max_attempts=200, tol=1e-12)
        if monthly_rate is None:
            raise ValueError("No se encontró tasa solución (quizás parámetros exigen tasas extremas).")

    # construir tabla de amortización en la tasa encontrada
    A = annuity_payment(principal, monthly_rate, n_months)
    table = []
    bal = principal
    for period in range(1, n_months + 1):
        start_bal = bal
        interest = start_bal * monthly_rate
        principal_repay = A - interest
        if principal_repay > bal:
            principal_repay = bal
            A = interest + principal_repay
        end_bal = max(start_bal - principal_repay, 0.0)
        table.append({
            'period': period,
            'start_balance': start_bal,
            'payment': A,
            'interest': interest,
            'principal_repayment': principal_repay,
            'end_balance': end_bal
        })
        bal = end_bal

    EAR = ((1 + monthly_rate)**12 - 1)*100  # Tasa Efectiva Anual

    return EAR,A
        #'monthly_rate': monthly_rate,
        #EAR, A #Interest rate and monthly payment
        #'amortization_table': table
    






