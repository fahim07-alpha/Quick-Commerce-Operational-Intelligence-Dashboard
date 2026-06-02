import pandas as pd 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error,r2_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,classification_report

df=pd.read_csv(r"C:\Users\lenovo\Downloads\project\Merged_data.csv")

# Train company-specific delivery models
# Create traffic levels BEFORE model training

df['Traffic_Level'] = df['Order_Hour'].apply(
    lambda x:
    'High' if 18 <= x <= 22
    else ('Medium' if 8 <= x <= 11 else 'Low')
)

# Train company-specific delivery models

company_models = {}

for company in sorted(df['Company'].unique()):

    company_df = df[df['Company'] == company]

    X_company = pd.get_dummies(
        company_df[
            [
                'Distance_Km',
                'Items_Count',
                'Order_Hour',
                'Traffic_Level',
                'City'
            ]
        ],
        drop_first=True
    )

    y_company = company_df['Delivery_Time_Min']

    model_company = LinearRegression()

    model_company.fit(X_company, y_company)

    company_models[company] = {
        'model': model_company,
        'columns': X_company.columns
    }

print(
    "Trained company-specific delivery models for:",
    list(company_models.keys())
)



# company_models = {}
# for company in sorted(df['Company'].unique()):
#     company_df = df[df['Company'] == company]
#     X_company = pd.get_dummies(company_df[['Distance_Km', 'Items_Count', 'Order_Hour', 'City', 'Peak_Time']], drop_first=True)
#     y_company = company_df['Delivery_Time_Min']
#     model_company = LinearRegression()
#     model_company.fit(X_company, y_company)
#     company_models[company] = {
#         'model': model_company,
#         'columns': X_company.columns
#     }

# print("Trained company-specific delivery models for:", list(company_models.keys()))

# Train company-specific discount models

df['Traffic_Level']=df['Order_Hour'].apply(lambda x: 'High' if 18<=x<=22 else ('Medium' if 8<=x<=11 else 'Low'))

company_discount_models = {}
for company in sorted(df['Company'].unique()):
    company_df = df[df['Company'] == company]
    A_company = pd.get_dummies(company_df[['Items_Count', 'Order_Hour', 'Traffic_Level', 'City', 'Order_Day']], drop_first=True)
    z_company = company_df['Discount_Applied']
    model_company = LogisticRegression(max_iter=1000, class_weight='balanced')
    model_company.fit(A_company, z_company)
    company_discount_models[company] = {
        'model': model_company,
        'columns': A_company.columns
    }

print("Trained company-specific discount models for:", list(company_discount_models.keys()))

A=pd.get_dummies(df[['Items_Count','Order_Hour','Traffic_Level','City','Company','Order_Day']],drop_first=True)
z=df['Discount_Applied']
A_train,A_test,z_train,z_test=train_test_split(A,z,test_size=0.2,random_state=42)
model=LogisticRegression(max_iter=1000,class_weight='balanced')
model.fit(A_train,z_train)
z_pred=model.predict(A_test)
print(z_pred)

print("Accuracy:",accuracy_score(z_test,z_pred))
print(classification_report(z_test,z_pred))

# bz=X.columns
# print(bz)