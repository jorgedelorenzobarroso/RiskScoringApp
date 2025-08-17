import streamlit as st
import plotly.graph_objects as go
from millify import millify
from streamlit_echarts import st_echarts
import pandas as pd
import numpy as np
import time
from Utils.Execution_Code import execute
from Utils.FunctionLibraryV1 import *

# -------------------
# PAGE CONFIG
# -------------------

st.markdown("""
    <style>
        /* Reducir padding del main */
        .block-container {
            padding-top: 2rem; /* antes suele ser ~6rem */
        }
    </style>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Risk Scoring Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# SIDEBAR CONFIGURATION
# ------------------------------

#Make header invisible
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            width: auto !important; 
            min-width: 350px;           
            max-width: 500px;           
        }

        [data-testid="stSidebarHeader"] {
            display : none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Add image to sidebar from the folder
#st.sidebar.image("Images/risk_score.jpg", use_container_width=True)


st.sidebar.title("Loan Application")

tab1, tab2, tab3 = st.sidebar.tabs(["Loan Details", "Applicant Info", "Market Factors"])

# ------------------------------
# Tab 1: Loan Details
# ------------------------------
with tab1:
    #st.subheader("Loan Details")
    num_installments = st.radio(
        "Number of Installments",
        options=['36', '60'],
        index=0
    )
    principal = st.number_input("Loan Amount (€)", min_value=0.0, value=10000.0, step=500.0)
    purpose = st.selectbox(
        "Purpose",
        options=['debt_consolidation', 'credit_card', 'home_improvement', 'medical',
                 'house', 'other', 'major_purchase', 'small_business', 'car',
                 'moving', 'wedding', 'vacation', 'renewable_energy', 'educational']
    )

# ------------------------------
# Tab 2: Applicant Info
# ------------------------------
with tab2:

    with st.expander(label = "Basic Information", expanded=False):
        
        #st.subheader("Applicant Info")
        income = st.number_input("Annual Income (€)", min_value=0.0, max_value=300000.0, value=60000.0, step=1000.0)
        income_verified = st.selectbox(
            "Income Verified",
            options=["Source Verified", "Verified", "Not Verified"]
        )
        employment_duration = st.selectbox(
            "Employment Duration",
            options=["1 year", "2 years", "3 years", "4 years", "5 years", "6 years", "7 years", "8 years", "9 years", "10+ years", "Unknown"]
        )
        housing = st.selectbox("Housing", options=['MORTGAGE', 'RENT', 'OWN', 'OTHER'])
        rating = st.selectbox("Credit Rating", options=["A", "B", "C", "D", "E", "F", "G","Unknown"])
        dti = st.number_input("Debt-to-Income Ratio (%)", min_value=0.0, value=30.0, step=5.0)

    # Additional fields for credit history
    with st.expander(label = "Credit History", expanded=False):
        num_mortgages = st.number_input("Number of Mortgages", min_value=0, value=1, step=1)
        num_credit_lines = st.number_input("Number of Credit Lines", min_value=0, value=1, step=1)
        num_cancellations_12m = st.number_input("Cancellations in Last 12 Months", min_value=0, value=1, step=1)
        num_derogatory_marks = st.number_input("Number of Derogatory Marks", min_value=0, value=1, step=1)
        months_since_last_delinquency = st.number_input("Months Since Last Delinquency", min_value=0, value=0, step=1)
        pct_cards_over_75p = st.number_input("Cards Over 75% Utilization (%)", min_value=0.0, value=20.0, step=5.0)
        pct_revolving_utilization = st.number_input("Revolving Utilization (%)", min_value=0.0, value=20.0, step=5.0)
        interest_rate = st.number_input("Interest Rate on Revolving (%)", min_value=0.0, value=10.0, step=1.0)
        installment_amount = st.number_input("Installment Amount (€)", min_value=0, value=100, step=5)
    

# ------------------------------
# Tab 3: Market Factors
# ------------------------------
with tab3:
    #st.subheader("Market Factors")
    euribor_6m = st.number_input("Euribor 6M (%)", min_value=-5.0, value=2.0, step=0.1)
    k_pct = st.number_input("K_pct (%)", min_value=0.0, value=0.5, step=0.1)
    r_capital = st.number_input("R Capital (%)", min_value=0.0, value=5.0, step=1.0)
    op_cost_rate = st.number_input("Operational Cost Rate (%)", min_value=0.0, value=0.5, step=0.1)
    margin_rate = st.number_input("Margin Rate (%)", min_value=0.0, value=0.5, step=0.1)


# Calculate button
calculate_pressed = st.sidebar.button("Calculate", type="primary")

# -------------------
# MAIN PAGE
# -------------------

# Add image from the folder
#st.image("Images/test3.png", use_container_width = 200)

st.title("Risk Scoring Analyzer")

if not calculate_pressed:
    st.markdown(
        """
        Please fill in the required information in the sidebar tabs and press **Calculate** 
        to generate the scoring metrics.
        """
    )
else:

    
    with st.spinner("Calculating risk score..."):
        pred = execute(pd.DataFrame({
            'income': income,
            'housing': housing,
            'purpose': purpose,
            'num_installments': num_installments,
            'num_cancellations_12m': num_cancellations_12m,
            'num_derogatory_marks': num_derogatory_marks,
            'income_verified': income_verified,
            'months_since_last_delinquency': months_since_last_delinquency,
            'employment_duration': employment_duration,
            'rating': rating,
            'dti': dti,
            'num_mortgages': num_mortgages,
            'num_credit_lines': num_credit_lines,
            'pct_cards_over_75p': pct_cards_over_75p,
            'pct_revolving_utilization': pct_revolving_utilization,
            'principal': principal,
            'interest_rate': interest_rate,
            'installment_amount': installment_amount}
            ,index=[0]))
        
        
        pred = pred.iloc[0]  # Get the first row of the DataFrame

        pd_value = pred.pd*100
        ead_value = pred.ead*100
        lgd_value = pred.lgd*100
        expected_loss_percent = pred.expected_loss * 100
        expected_loss_eur = round(pred.expected_loss_euro)

        
        tae_percent, monthly_payment_eur = price_rate_and_payment(
            principal=principal,
            n_months=int(num_installments),
            EL_rate=expected_loss_percent/ 100,
            euribor_annual=euribor_6m/ 100,
            K_pct=k_pct / 100,
            r_capital= r_capital / 100,
            op_cost_rate= op_cost_rate / 100,
            margin_rate= margin_rate / 100,
            verbose=False
        )


        option = {
        "series": [
            {
                "type": "gauge",
                "startAngle": 180,
                "endAngle": 0,
                "min": 0,
                "max": 100,
                "progress": {"show": True, "width": 18},
                "pointer": {"show": True},
                "detail": {"formatter": "{value}"},
                "data": [{"value": 65, "name": "LGD"}],
                "axisLine": {"lineStyle": {"width": 18}},
            }
        ]
        }


        # Create Gauge charts
        def create_gauge(value, title, color):
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': title, 'font': {'size': 25}},
                gauge={
                    'axis': {'range': [0, 100],
                                # 'tickvals': [],  # Sin posiciones de ticks
                            'ticktext': [],
                            'tickfont': {'color': 'rgba(0,0,0,0)'}
                            },
                    'bar': {'color': color},
                    'bgcolor': "white",
                    # 'steps': [
                    #     {'range': [0, 99], 'color': "lightgray"},
                    #     # {'range': [25, 50], 'color': "lightgray"},
                    #     # {'range': [50, 75], 'color': "lightgray"},
                    #     # {'range': [75, 100], 'color': "lightgray"}
                    # ],
                }
            ))

            fig.update_layout(
                margin=dict(l=10, r=10, t=100, b=20),  # Reduce márgenes del gráfico
                height=250,  # Ajusta la altura si quieres
                width=250    # Ajusta el ancho si quieres
            )
            return fig
        


        col1, col2, col3 = st.columns(3)
        #with st.container(horizontal = True,horizontal_alignment="right", vertical_alignment="center"):
        with col1:
            st.plotly_chart(create_gauge(pd_value, "Probability of Default", "red"), use_container_width=True)

            formatted_loss = millify(expected_loss_eur, precision=2)

            col11, col12 = st.columns([7, 25])

            with col12:

                st.metric("Expected Loss", f"{expected_loss_percent:.2f}% (€{formatted_loss})")

        with col2:
            st.plotly_chart(create_gauge(ead_value, "Exposure at Default", "red"), use_container_width=True)

            col21, col22 = st.columns([10, 23])

            with col22:

                st.metric("Recommended EAR", f"{tae_percent:.2f}%")

        with col3:
            st.plotly_chart(create_gauge(lgd_value, "Loss Given Default", "red"), use_container_width=True)

            col31, col32 = st.columns([10, 25])

            with col32:

                st.metric("Monthly Payment", f"€{monthly_payment_eur:,.2f}")


        
