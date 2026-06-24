import pandas as pd

def calculate_metrics(df):

    df["revenue"] = df["unit_price"] * df["quantity"]

    total_revenue = df["revenue"].sum()
    total_orders = df["order_id"].nunique()
    avg_order_value = total_revenue / total_orders

    return {
        "Total Revenue": total_revenue,
        "Total Orders": total_orders,
        "Average Order Value": avg_order_value
    }

if __name__ == "__main__":
    data = {
        "order_id": [1, 2, 3],
        "unit_price": [100, 200, 300],
        "quantity": [2, 3, 4]
    }

    df = pd.DataFrame(data)

    metrics = calculate_metrics(df)
    print(metrics)
