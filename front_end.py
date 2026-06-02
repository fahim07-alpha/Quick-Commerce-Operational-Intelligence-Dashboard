import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

# Load data and train models
df = pd.read_csv(r"Merged_data.csv")

# Derived features match the logic in prediction.py

def derive_peak_time(order_hour):
    return 'Peak' if order_hour in [22, 23] else 'Non Peak'


def derive_traffic_level(order_hour):
    if 18 <= order_hour <= 22:
        return 'High'
    if 8 <= order_hour <= 11:
        return 'Medium'
    return 'Low'

# Model 1: Delivery Time Prediction
X = pd.get_dummies(df[['Distance_Km', 'Items_Count', 'Order_Hour', 'Company', 'City', 'Peak_Time']], drop_first=True)
y = df['Delivery_Time_Min']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model1 = LinearRegression()
model1.fit(X_train, y_train)

# Model 2: Discount Prediction
A = pd.get_dummies(df[['Items_Count', 'Order_Hour', 'Traffic_Level', 'City', 'Company', 'Order_Day']], drop_first=True)
z = df['Discount_Applied']
A_train, A_test, z_train, z_test = train_test_split(A, z, test_size=0.2, random_state=42)
model2 = LogisticRegression(max_iter=1000, class_weight='balanced')
model2.fit(A_train, z_train)

class DeliveryPredictionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚚 Delivery Prediction System - AI Analytics Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Set style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#1a1a1a')
        style.configure('TFrame', background='#1a1a1a')
        style.configure('TLabel', background='#1a1a1a', foreground='white')
        style.configure('TLabelframe', background='#1a1a1a', foreground='white')
        style.configure('TLabelframe.Label', background='#1a1a1a', foreground='#00bfff')
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Dashboard
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text="📊 Dashboard")
        self.create_dashboard_tab()
        
        # Tab 2: Delivery Time
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="📦 Delivery Time Prediction")
        self.create_delivery_tab()
        
        # Tab 3: Discount
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="💰 Discount Prediction")
        self.create_discount_tab()
        
    def create_dashboard_tab(self):
        # Create main frame
        main_frame = ttk.Frame(self.tab_dashboard)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill='x', pady=10)
        
        # Create stat boxes
        stat_boxes = [
            (f"Total Orders: {len(df)}", "#00bfff"),
            (f"Avg Delivery: {df['Delivery_Time_Min'].mean():.1f} min", "#00ff00"),
            (f"Avg Distance: {df['Distance_Km'].mean():.1f} km", "#ff6b6b"),
            (f"Discounts: {(df['Discount_Applied'].sum()/len(df)*100):.1f}%", "#fFA500"),
        ]
        
        for text, color in stat_boxes:
            label = ttk.Label(stats_frame, text=text, foreground=color, font=('Arial', 12, 'bold'))
            label.pack(side='left', padx=20)
        
        # Charts frame
        charts_frame = ttk.Frame(main_frame)
        charts_frame.pack(fill='both', expand=True)
        
        # Create figure with subplots
        fig = Figure(figsize=(14, 5.5), dpi=100, facecolor='#1a1a1a')
        
        # Chart 1: Delivery time by distance
        ax1 = fig.add_subplot(1, 3, 1)
        delivery_data = df.groupby(pd.cut(df['Distance_Km'], bins=5))['Delivery_Time_Min'].mean()
        labels = [f"{int(x.left)}-{int(x.right)}" for x in delivery_data.index]
        ax1.plot(labels, delivery_data.values, marker='o', color='#00bfff', linewidth=2, markersize=8)
        ax1.set_title('Delivery Time by Distance', color='#00bfff', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Distance Range (km)', color='white')
        ax1.set_ylabel('Time (min)', color='white')
        ax1.tick_params(colors='white')
        ax1.set_facecolor('#2a2a2a')
        ax1.grid(True, alpha=0.2, color='white')
        
        # Chart 2: Orders by company
        ax2 = fig.add_subplot(1, 3, 2)
        company_counts = df['Company'].value_counts()
        colors = ['#00bfff', '#00ff00', '#ff6b6b', '#ffa500', '#ff00ff']
        ax2.pie(company_counts.values, labels=company_counts.index, autopct='%1.1f%%', 
                colors=colors[:len(company_counts)], textprops={'color': 'white'})
        ax2.set_title('Orders by Company', color='#00bfff', fontsize=12, fontweight='bold')
        ax2.set_facecolor('#2a2a2a')
        
        # Chart 3: Discount by hour
        ax3 = fig.add_subplot(1, 3, 3)
        discount_by_hour = df.groupby('Order_Hour')['Discount_Applied'].mean() * 100
        ax3.bar(range(24), discount_by_hour.values, color='#ffa500', alpha=0.7)
        ax3.set_title('Discount Rate by Hour', color='#00bfff', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Hour (24h)', color='white')
        ax3.set_ylabel('Discount Rate (%)', color='white')
        ax3.tick_params(colors='white')
        ax3.set_facecolor('#2a2a2a')
        ax3.grid(True, alpha=0.2, axis='y', color='white')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_delivery_tab(self):
        # Main frame with black background
        main_frame = ttk.Frame(self.tab1)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Form
        left_frame = ttk.LabelFrame(main_frame, text="Prediction Form", padding=20)
        left_frame.pack(side='left', fill='both', padx=5, pady=5)
        
        # Distance input
        ttk.Label(left_frame, text="Distance (Km):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.distance_var = tk.DoubleVar(value=5.0)
        distance_frame = ttk.Frame(left_frame)
        distance_frame.pack(fill='x', pady=5)
        ttk.Scale(distance_frame, from_=0.1, to=50.0, orient='horizontal', variable=self.distance_var, command=self.update_distance_label).pack(side='left', fill='x', expand=True, padx=5)
        self.distance_label = ttk.Label(distance_frame, text="5.0 km", foreground='#00ff00', font=('Arial', 10, 'bold'))
        self.distance_label.pack(side='left', padx=5)
        
        # Items count input
        ttk.Label(left_frame, text="Number of Items:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.items_count_var = tk.IntVar(value=5)
        ttk.Spinbox(left_frame, from_=1, to=100, textvariable=self.items_count_var, width=10).pack(anchor='w', pady=5)
        
        # Order hour input
        ttk.Label(left_frame, text="Order Hour (0-23):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.order_hour_var = tk.IntVar(value=12)
        hour_frame = ttk.Frame(left_frame)
        hour_frame.pack(fill='x', pady=5)
        ttk.Scale(hour_frame, from_=0, to=23, orient='horizontal', variable=self.order_hour_var, command=self.update_hour_label).pack(side='left', fill='x', expand=True, padx=5)
        self.hour_label = ttk.Label(hour_frame, text="12:00", foreground='#00ff00', font=('Arial', 10, 'bold'))
        self.hour_label.pack(side='left', padx=5)
        
        # Company dropdown
        ttk.Label(left_frame, text="Company:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.company_var = tk.StringVar()
        company_dropdown = ttk.Combobox(left_frame, textvariable=self.company_var, values=sorted(df['Company'].unique()), state='readonly')
        company_dropdown.pack(fill='x', pady=5)
        company_dropdown.current(0)
        
        # Predict button
        predict_btn = tk.Button(left_frame, text="🔮 Predict Delivery Time", command=self.predict_delivery, 
                               bg='#00bfff', fg='black', font=('Arial', 11, 'bold'), padx=20, pady=10, cursor='hand2')
        predict_btn.pack(fill='x', pady=15)
        
        # Result display
        self.delivery_result = ttk.Label(left_frame, text="", font=('Arial', 12, 'bold'), foreground='#00ff00')
        self.delivery_result.pack(pady=10)
        
        # Right panel - Visualization
        right_frame = ttk.LabelFrame(main_frame, text="Delivery Analysis", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        self.delivery_canvas = tk.Canvas(right_frame, bg='#2a2a2a', highlightthickness=0)
        self.delivery_canvas.pack(fill='both', expand=True)
        
        self.draw_delivery_chart()
    
    def create_discount_tab(self):
        # Main frame
        main_frame = ttk.Frame(self.tab2)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Form
        left_frame = ttk.LabelFrame(main_frame, text="Prediction Form", padding=20)
        left_frame.pack(side='left', fill='both', padx=5, pady=5)
        
        # Items count input
        ttk.Label(left_frame, text="Number of Items:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.discount_items_var = tk.IntVar(value=5)
        ttk.Spinbox(left_frame, from_=1, to=100, textvariable=self.discount_items_var, width=10).pack(anchor='w', pady=5)
        
        # Order hour input
        ttk.Label(left_frame, text="Order Hour (0-23):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.discount_hour_var = tk.IntVar(value=12)
        hour_frame = ttk.Frame(left_frame)
        hour_frame.pack(fill='x', pady=5)
        ttk.Scale(hour_frame, from_=0, to=23, orient='horizontal', variable=self.discount_hour_var, command=self.update_discount_hour_label).pack(side='left', fill='x', expand=True, padx=5)
        self.discount_hour_label = ttk.Label(hour_frame, text="12:00", foreground='#00ff00', font=('Arial', 10, 'bold'))
        self.discount_hour_label.pack(side='left', padx=5)
        
        # City dropdown
        ttk.Label(left_frame, text="City:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(left_frame, textvariable=self.city_var, values=sorted(df['City'].unique()), state='readonly')
        city_dropdown.pack(fill='x', pady=5)
        city_dropdown.current(0)
        
        # Company dropdown
        ttk.Label(left_frame, text="Company:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.discount_company_var = tk.StringVar()
        company_dropdown = ttk.Combobox(left_frame, textvariable=self.discount_company_var, values=sorted(df['Company'].unique()), state='readonly')
        company_dropdown.pack(fill='x', pady=5)
        company_dropdown.current(0)
        
        # Order day dropdown
        ttk.Label(left_frame, text="Order Day:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.order_day_var = tk.StringVar()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_dropdown = ttk.Combobox(left_frame, textvariable=self.order_day_var, values=days, state='readonly')
        day_dropdown.pack(fill='x', pady=5)
        day_dropdown.current(0)
        
        # Predict button
        predict_btn = tk.Button(left_frame, text="🔮 Predict Discount", command=self.predict_discount,
                               bg='#ffa500', fg='black', font=('Arial', 11, 'bold'), padx=20, pady=10, cursor='hand2')
        predict_btn.pack(fill='x', pady=15)
        
        # Result display
        self.discount_result = ttk.Label(left_frame, text="", font=('Arial', 12, 'bold'))
        self.discount_result.pack(pady=10)
        
        # Right panel - Visualization
        right_frame = ttk.LabelFrame(main_frame, text="Discount Analysis", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        self.discount_canvas = tk.Canvas(right_frame, bg='#2a2a2a', highlightthickness=0)
        self.discount_canvas.pack(fill='both', expand=True)
        
        self.draw_discount_chart()
    
    def update_distance_label(self, val):
        self.distance_label.config(text=f"{float(val):.1f} km")
    
    def update_hour_label(self, val):
        self.hour_label.config(text=f"{int(float(val)):02d}:00")
    
    def update_discount_hour_label(self, val):
        self.discount_hour_label.config(text=f"{int(float(val)):02d}:00")
    
    def draw_delivery_chart(self):
        self.delivery_canvas.delete("all")
        
        # Create plot
        fig = Figure(figsize=(5.5, 5), dpi=80, facecolor='#2a2a2a')
        ax = fig.add_subplot(111)
        
        delivery_data = df.groupby(pd.cut(df['Distance_Km'], bins=5))['Delivery_Time_Min'].mean()
        labels = [f"{int(x.left)}-{int(x.right)}" for x in delivery_data.index]
        
        ax.bar(labels, delivery_data.values, color='#00bfff', alpha=0.7)
        ax.set_title('Average Delivery Time by Distance', color='#00bfff', fontsize=11, fontweight='bold')
        ax.set_ylabel('Time (minutes)', color='white')
        ax.tick_params(colors='white')
        ax.set_facecolor('#2a2a2a')
        ax.grid(True, alpha=0.2, axis='y', color='white')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.delivery_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def draw_discount_chart(self):
        self.discount_canvas.delete("all")
        
        # Create plot
        fig = Figure(figsize=(5.5, 5), dpi=80, facecolor='#2a2a2a')
        ax = fig.add_subplot(111)
        
        discount_by_city = df.groupby('City')['Discount_Applied'].mean() * 100
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(discount_by_city)))
        ax.bar(range(len(discount_by_city)), discount_by_city.values, color='#ffa500', alpha=0.7)
        ax.set_xticks(range(len(discount_by_city)))
        ax.set_xticklabels(discount_by_city.index, rotation=45, ha='right', color='white')
        ax.set_title('Discount Rate by City', color='#ffa500', fontsize=11, fontweight='bold')
        ax.set_ylabel('Discount Rate (%)', color='white')
        ax.tick_params(colors='white')
        ax.set_facecolor('#2a2a2a')
        ax.grid(True, alpha=0.2, axis='y', color='white')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.discount_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def predict_delivery(self):
        try:
            distance = self.distance_var.get()
            items_count = self.items_count_var.get()
            order_hour = self.order_hour_var.get()
            company = self.company_var.get()
            
            if not company:
                messagebox.showerror("Error", "Please select a company")
                return
            
            # Prepare input data with derived peak time feature
            peak_time = derive_peak_time(order_hour)
            input_data = pd.DataFrame({
                'Distance_Km': [distance],
                'Items_Count': [items_count],
                'Order_Hour': [order_hour],
                'Company': [company],
                'City': [self.city_var.get()],
                'Peak_Time': [peak_time]
            })
            
            # One-hot encode
            input_encoded = pd.get_dummies(input_data, drop_first=True)
            X_full = pd.get_dummies(df[['Distance_Km', 'Items_Count', 'Order_Hour', 'Company', 'City', 'Peak_Time']], drop_first=True)
            
            for col in X_full.columns:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[X_full.columns]
            
            # Get prediction
            prediction = model1.predict(input_encoded)[0]
            self.delivery_result.config(text=f"✓ {prediction:.1f} minutes", foreground='#00ff00')
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed: {str(e)}")
    
    def predict_discount(self):
        try:
            items_count = self.discount_items_var.get()
            order_hour = self.discount_hour_var.get()
            city = self.city_var.get()
            company = self.discount_company_var.get()
            order_day = self.order_day_var.get()
            
            if not city or not company or not order_day:
                messagebox.showerror("Error", "Please select all fields")
                return
            
            # Prepare input data with derived traffic level
            traffic_level = derive_traffic_level(order_hour)
            input_data = pd.DataFrame({
                'Items_Count': [items_count],
                'Order_Hour': [order_hour],
                'Traffic_Level': [traffic_level],
                'City': [city],
                'Company': [company],
                'Order_Day': [order_day]
            })
            
            # One-hot encode
            input_encoded = pd.get_dummies(input_data, drop_first=True)
            A_full = pd.get_dummies(df[['Items_Count', 'Order_Hour', 'Traffic_Level', 'City', 'Company', 'Order_Day']], drop_first=True)
            
            for col in A_full.columns:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[A_full.columns]
            
            # Get prediction
            discount_pred = model2.predict(input_encoded)[0]
            prob = model2.predict_proba(input_encoded)[0]
            confidence = prob[int(discount_pred)] * 100
            
            if discount_pred == 1:
                self.discount_result.config(text=f"✓ Eligible! ({confidence:.1f}%)", foreground='#00ff00')
            else:
                self.discount_result.config(text=f"✗ Not Eligible ({confidence:.1f}%)", foreground='#ff6b6b')
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeliveryPredictionApp(root)
    root.mainloop()
