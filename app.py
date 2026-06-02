from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
import json
import webbrowser

app = Flask(__name__, template_folder='templates')

# Load data
df = pd.read_csv(r"Merged_data.csv")

# Train models
X = pd.get_dummies(df[['Distance_Km', 'Items_Count', 'Order_Hour', 'Company', 'City', 'Order_Value']], drop_first=True)
y = df['Delivery_Time_Min']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model1 = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model1.fit(X_train, y_train)

A = pd.get_dummies(df[['Items_Count', 'Order_Hour', 'City', 'Company', 'Order_Day']], drop_first=True)
z = df['Discount_Applied']
A_train, A_test, z_train, z_test = train_test_split(A, z, test_size=0.2, random_state=42)
model2 = LogisticRegression(max_iter=1000, class_weight='balanced')
model2.fit(A_train, z_train)

# Create Traffic_Level feature used by company-specific models
df['Traffic_Level'] = df['Order_Hour'].apply(
    lambda x: 'High' if 18 <= x <= 22 else ('Medium' if 8 <= x <= 11 else 'Low')
)

# Train company-specific delivery and discount models
company_models = {}
for company in sorted(df['Company'].unique()):
    company_df = df[df['Company'] == company]
    X_company = pd.get_dummies(
        company_df[[
            'Distance_Km',
            'Items_Count',
            'Order_Hour',
            'Traffic_Level',
            'City'
        ]],
        drop_first=True
    )
    y_company = company_df['Delivery_Time_Min']
    model_company = LinearRegression()
    model_company.fit(X_company, y_company)
    company_models[company] = {
        'model': model_company,
        'columns': X_company.columns
    }

company_discount_models = {}
for company in sorted(df['Company'].unique()):
    company_df = df[df['Company'] == company]
    A_company = pd.get_dummies(company_df[['Items_Count', 'Order_Hour', 'Traffic_Level', 'City', 'Order_Day']], drop_first=True)
    z_company = company_df['Discount_Applied']
    disc_model = LogisticRegression(max_iter=1000, class_weight='balanced')
    disc_model.fit(A_company, z_company)
    company_discount_models[company] = {
        'model': disc_model,
        'columns': A_company.columns
    }

@app.route('/')
def index():
    # Calculate stats
    best_rated_company = df.groupby('Company')['Customer_Rating'].mean().idxmax()
    fastest_delivery_company = df.groupby('Company')['Delivery_Time_Min'].mean().idxmin()
    most_overloaded_region = 'Rajajinagar'

    stats = {
        'total_orders': len(df),
        'avg_delivery_time': round(df['Delivery_Time_Min'].mean(), 1),
        'avg_distance': round(df['Distance_Km'].mean(), 1),
        'discount_percentage': round((df['Discount_Applied'].sum() / len(df) * 100), 1),
        'companies': sorted(df['Company'].unique().tolist()),
        'cities': sorted(df['City'].unique().tolist()),
        'peak_times': sorted(df['Peak_Time'].unique().tolist()),
        'order_days': sorted(df['Order_Day'].unique().tolist(), key=lambda x: ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].index(x)),
        'avg_rating': round(df['Customer_Rating'].mean(), 1),
        'total_revenue': int(df['Order_Value'].sum()),
        'best_rated_company': best_rated_company,
        'most_overloaded_region': most_overloaded_region,
        'fastest_delivery_company': fastest_delivery_company,
    }
    return render_template('index.html', stats=stats)

@app.route('/api/get-charts')
def get_charts():
    """Enhanced analytics charts with business insights"""
    
    # 1. Peak Hours Analysis - Delivery time by hour
    hourly_delivery = df.groupby('Order_Hour').agg({
        'Delivery_Time_Min': 'mean',
        'Order_ID': 'count',
        'Customer_Rating': 'mean'
    }).reset_index()
    delivery_by_hour = {
        'labels': [f"{int(h):02d}:00" for h in hourly_delivery['Order_Hour']],
        'data': hourly_delivery['Delivery_Time_Min'].round(1).tolist(),
        'orders': hourly_delivery['Order_ID'].tolist(),
        'ratings': hourly_delivery['Customer_Rating'].round(2).tolist()
    }
    
    # 2. Delivery Efficiency - Distance vs Delivery Time (scatter data)
    distance_bins = pd.cut(df['Distance_Km'], bins=10)
    efficiency_data = df.groupby(distance_bins).agg({
        'Delivery_Time_Min': 'mean',
        'Distance_Km': 'mean',
        'Order_ID': 'count'
    }).reset_index(drop=True)
    delivery_efficiency = {
        'labels': [f"{dist:.1f}km" for dist in efficiency_data['Distance_Km'].values],
        'delivery_times': efficiency_data['Delivery_Time_Min'].round(1).tolist(),
        'distances': efficiency_data['Distance_Km'].round(1).tolist(),
        'orders_count': efficiency_data['Order_ID'].tolist()
    }
    
    # 3. Revenue Analysis by Company
    revenue_by_company = df.groupby('Company').agg({
        'Order_Value': 'sum',
        'Order_ID': 'count',
        'Delivery_Time_Min': 'mean'
    }).sort_values('Order_Value', ascending=False).reset_index()
    company_revenue = {
        'labels': revenue_by_company['Company'].tolist(),
        'revenue': revenue_by_company['Order_Value'].tolist(),
        'orders': revenue_by_company['Order_ID'].tolist(),
        'avg_delivery': revenue_by_company['Delivery_Time_Min'].round(1).tolist()
    }
    
    # 4. Customer Satisfaction Distribution
    rating_dist = df['Customer_Rating'].value_counts().sort_index()
    satisfaction = {
        'labels': [str(int(r)) for r in rating_dist.index],
        'data': rating_dist.values.tolist()
    }
    
    # 5. Dark Store Impact on Delivery Time
    dark_store_impact = df.groupby(pd.cut(df['No_of_Dark_Stores'], bins=[-1, 0, 2, 5, 10])).agg({
        'Delivery_Time_Min': 'mean',
        'Order_ID': 'count',
        'Customer_Rating': 'mean'
    }).reset_index()
    dark_store_impact['Store_Range'] = ['No Dark Store', '1-2 Stores', '3-5 Stores', '6+ Stores']
    dark_stores = {
        'labels': dark_store_impact['Store_Range'].tolist(),
        'delivery_time': dark_store_impact['Delivery_Time_Min'].round(1).tolist(),
        'orders': dark_store_impact['Order_ID'].tolist(),
        'ratings': dark_store_impact['Customer_Rating'].round(2).tolist()
    }
    
    # 6. Peak vs Non-Peak Performance
    peak_comparison = df.groupby('Peak_Time').agg({
        'Delivery_Time_Min': ['mean', 'std'],
        'Order_ID': 'count',
        'Customer_Rating': 'mean',
        'Order_Value': 'mean'
    }).reset_index()
    peak_performance = {
        'labels': peak_comparison['Peak_Time'].tolist(),
        'avg_delivery': peak_comparison[('Delivery_Time_Min', 'mean')].round(1).tolist(),
        'std_delivery': peak_comparison[('Delivery_Time_Min', 'std')].round(1).tolist(),
        'avg_rating': peak_comparison[('Customer_Rating', 'mean')].round(2).tolist(),
        'avg_order_value': peak_comparison[('Order_Value', 'mean')].round(0).tolist(),
        'total_orders': peak_comparison[('Order_ID', 'count')].tolist()
    }
    
    # 7. Top Cities Performance
    city_perf = df.groupby('City').agg({
        'Delivery_Time_Min': 'mean',
        'Order_ID': 'count',
        'Customer_Rating': 'mean',
        'Order_Value': 'mean'
    }).sort_values('Order_ID', ascending=False).head(8).reset_index()
    city_performance = {
        'labels': city_perf['City'].tolist(),
        'delivery_times': city_perf['Delivery_Time_Min'].round(1).tolist(),
        'orders': city_perf['Order_ID'].tolist(),
        'ratings': city_perf['Customer_Rating'].round(2).tolist()
    }
    
    # 8. Customer Rating by Company
    rating_by_company_df = df.groupby('Company')['Customer_Rating'].mean().sort_values(ascending=False).reset_index()
    rating_by_company = {
        'labels': rating_by_company_df['Company'].tolist(),
        'ratings': rating_by_company_df['Customer_Rating'].round(2).tolist()
    }

    # 9. Top 10 Overloaded Dark Store Regions
    demand = df.groupby(['Company', 'City']).size().reset_index(name='Total_Orders')
    stores = df.groupby(['Company', 'City'])['No_of_Dark_Stores'].first().reset_index()
    comparison = demand.merge(stores, on=['Company', 'City'])
    valid_comparison = comparison[comparison['No_of_Dark_Stores'] > 0].copy()
    valid_comparison['Demand_per_Store'] = valid_comparison['Total_Orders'] / valid_comparison['No_of_Dark_Stores']
    top_regions = valid_comparison.sort_values('Demand_per_Store', ascending=False).head(10).reset_index(drop=True)
    overloaded_darkstore_regions = {
        'labels': (top_regions['Company'] + ' - ' + top_regions['City']).tolist(),
        'demand_per_store': top_regions['Demand_per_Store'].round(1).tolist(),
        'total_orders': top_regions['Total_Orders'].tolist(),
        'dark_stores': top_regions['No_of_Dark_Stores'].tolist()
    }

    # 10. Operational Load vs Delivery Efficiency
    analysis = valid_comparison.copy()
    delivery_avg = df.groupby(['Company', 'City'])['Delivery_Time_Min'].mean().reset_index(name='Avg_Delivery_Time')
    analysis = analysis.merge(delivery_avg, on=['Company', 'City'])
    operational_load_efficiency = {
        'points': [
            {
                'company': row['Company'],
                'city': row['City'],
                'demand_per_store': round(row['Demand_per_Store'], 1),
                'avg_delivery_time': round(row['Avg_Delivery_Time'], 1),
                'total_orders': int(row['Total_Orders'])
            }
            for _, row in analysis.iterrows()
        ]
    }

    # 11. Items Count Impact
    items_impact = df.groupby(pd.cut(df['Items_Count'], bins=6)).agg({
        'Delivery_Time_Min': 'mean',
        'Order_ID': 'count',
        'Customer_Rating': 'mean'
    }).reset_index()
    items_impact['Item_Range'] = [f"{int(x.left)}-{int(x.right)}" for x in items_impact['Items_Count']]
    items_analysis = {
        'labels': items_impact['Item_Range'].tolist(),
        'delivery_time': items_impact['Delivery_Time_Min'].round(1).tolist(),
        'orders': items_impact['Order_ID'].tolist(),
        'ratings': items_impact['Customer_Rating'].round(2).tolist()
    }
    
    # 9. Order Value vs Customer Rating
    rating_ranges = pd.cut(df['Customer_Rating'], bins=5)
    value_by_rating = df.groupby(rating_ranges).agg({
        'Order_Value': 'mean',
        'Order_ID': 'count'
    }).reset_index()
    value_rating = {
        'labels': [f"{int(x.left)}-{int(x.right)}" for x in value_by_rating['Customer_Rating']],
        'values': value_by_rating['Order_Value'].round(0).tolist(),
        'orders': value_by_rating['Order_ID'].tolist()
    }
    
    # 10. Category Distribution with Performance
    category_perf = df.groupby('Product_Category').agg({
        'Order_ID': 'count',
        'Delivery_Time_Min': 'mean',
        'Customer_Rating': 'mean',
        'Order_Value': 'mean'
    }).sort_values('Order_ID', ascending=False).head(8).reset_index()
    category_analysis = {
        'labels': category_perf['Product_Category'].tolist(),
        'orders': category_perf['Order_ID'].tolist(),
        'delivery_time': category_perf['Delivery_Time_Min'].round(1).tolist(),
        'ratings': category_perf['Customer_Rating'].round(2).tolist()
    }
    
    return jsonify({
        'delivery_by_hour': delivery_by_hour,
        'delivery_efficiency': delivery_efficiency,
        'company_revenue': company_revenue,
        'satisfaction': satisfaction,
        'dark_stores': dark_stores,
        'peak_performance': peak_performance,
        'city_performance': city_performance,
        'rating_by_company': rating_by_company,
        'overloaded_darkstore_regions': overloaded_darkstore_regions,
        'operational_load_efficiency': operational_load_efficiency,
        'items_analysis': items_analysis,
        'value_rating': value_rating,
        'category_analysis': category_analysis
    })

@app.route('/api/predict-delivery', methods=['POST'])
def predict_delivery():
    """Predict delivery time based on input parameters. Use company-specific model when available."""
    try:
        data = request.json

        # Prepare data for model
        distance = data.get('distance', 5)
        items_count = data.get('items_count', 5)
        order_hour = data.get('order_hour', 12)
        company = data.get('company', df['Company'].iloc[0])
        city = data.get('city', df['City'].iloc[0])

        # Compute traffic level consistent with training
        traffic_level = 'High' if 18 <= int(order_hour) <= 22 else ('Medium' if 8 <= int(order_hour) <= 11 else 'Low')

        # Try company-specific model first
        if company in company_models:
            cols = company_models[company]['columns']
            input_data = pd.DataFrame({
                'Distance_Km': [distance],
                'Items_Count': [items_count],
                'Order_Hour': [order_hour],
                'Traffic_Level': [traffic_level],
                'City': [city]
            })
            input_encoded = pd.get_dummies(input_data, drop_first=True)
            for col in cols:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[cols]
            prediction = company_models[company]['model'].predict(input_encoded)[0]
            traffic_status = "Low"

            if 18 <= order_hour <= 21:
                prediction += 3.5
                traffic_status = "High"

            elif 12 <= order_hour <= 14:
                prediction += 2
                traffic_status = "Medium"

            elif 7 <= order_hour <= 9:
                prediction += 1.2
                traffic_status = "Medium"

            elif 22 <= order_hour <= 23 or 0 <= order_hour <= 5:
                prediction -= 0.8
                traffic_status = "Low"

            if distance <= 1.5:
                prediction -= 1.5

            if distance <= 2:
                prediction -= 3

            elif distance <= 5:
                prediction -= 1.5

            elif distance >= 10:
                prediction += 2

            elif distance >= 15:
                prediction += 4

            # company efficiency adjustment

            if company == "Blinkit":
                prediction -= 1.2

            elif company == "Zepto":
                prediction -= 1

            elif company == "Swiggy Instamart":
                prediction += 0.5

            elif company == "Amazon Now":
                prediction += 1

            elif company == "Big Basket":
                prediction += 1.5

            city_adjustment = {
                "Whitefield": 2,
                "Marathahalli": 1.5,
                "Koramangala": 1,
                "Sarjapur": 1.8,
                "Indiranagar": 0.5,
                "Rajajinagar": 0.3,
                "Banashankari": 0.2,
                "Kr Puram": 1.7
            }

            prediction += city_adjustment.get(city, 0)

            prediction = max(prediction, 8)
            
            prediction = round(prediction, 1)
        else:
            # fallback to global model
            order_value = data.get('order_value', round(df['Order_Value'].mean(), 1))
            input_data = pd.DataFrame({
                'Distance_Km': [distance],
                'Items_Count': [items_count],
                'Order_Hour': [order_hour],
                'Company': [company],
                'City': [city],
                'Order_Value': [order_value]
            })
            input_encoded = pd.get_dummies(input_data, drop_first=True)
            for col in X.columns:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[X.columns]
            prediction = model1.predict(input_encoded)[0]

        average_delivery = df['Delivery_Time_Min'].mean()
        delta = round(prediction - average_delivery, 1)
        trend = 'faster than average' if delta < 0 else 'slower than average' if delta > 0 else 'at the average pace'

        return jsonify({
            'success': True,
            'prediction': round(prediction, 1),
            'difference': round(delta, 1),
            'trend': trend,
            'avg_delivery': round(average_delivery, 1),
            'traffic_status': traffic_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/predict-discount', methods=['POST'])
def predict_discount():
    """Predict discount eligibility"""
    try:
        data = request.json
        
        items_count = data.get('items_count', 5)
        order_hour = data.get('order_hour', 12)
        city = data.get('city', df['City'].iloc[0])
        company = data.get('company', df['Company'].iloc[0])
        order_day = data.get('order_day', 'Monday')

        # Compute traffic level
        traffic_level = 'High' if 18 <= int(order_hour) <= 22 else ('Medium' if 8 <= int(order_hour) <= 11 else 'Low')

        # Try company-specific discount model first
        if company in company_discount_models:
            cols = company_discount_models[company]['columns']
            input_data = pd.DataFrame({
                'Items_Count': [items_count],
                'Order_Hour': [order_hour],
                'Traffic_Level': [traffic_level],
                'City': [city],
                'Order_Day': [order_day]
            })
            input_encoded = pd.get_dummies(input_data, drop_first=True)
            for col in cols:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[cols]
            prediction = company_discount_models[company]['model'].predict(input_encoded)[0]
            confidence = round(max(company_discount_models[company]['model'].predict_proba(input_encoded)[0]) * 100, 1)
        else:
            # fallback to global discount model
            input_data = pd.DataFrame({
                'Items_Count': [items_count],
                'Order_Hour': [order_hour],
                'City': [city],
                'Company': [company],
                'Order_Day': [order_day]
            })
            input_encoded = pd.get_dummies(input_data, drop_first=True)
            for col in A.columns:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[A.columns]
            prediction = model2.predict(input_encoded)[0]
            confidence = round(max(model2.predict_proba(input_encoded)[0]) * 100, 1)

        return jsonify({
            'success': True,
            'eligible': bool(prediction),
            'confidence': confidence
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    url = "http://127.0.0.1:5000"
    webbrowser.open_new(url)
    app.run(debug=True, port=5000, use_reloader=False)
