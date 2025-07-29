

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field,validator
from enum import Enum
from typing import List,Optional
from decimal import Decimal
from uuid import uuid4
import uvicorn

app=FastAPI()

class FoodCategory(str,Enum):
    appetizer="Appetizer"
    main_course="Main Course"
    dessert="Dessert"
    beverage="Beverage"


class OrderStatus(str,Enum):
    pending="Pending"
    preparing="Preparing"
    delivered="Delivered"
    cancelled="Cancelled"






menu_db={}
orders_db={}
menu_id_counter=1


class FoodItem(BaseModel):
    id:int
    name: str=Field(..., min_length=3,max_length=100)
    description: str=Field(..., min_length=10,max_length=500)
    catergory:FoodCategory
    price:Decimal=Field(...,gt=0,max_digits=5,decimal_places=2)
    is_available:bool=True
    preparation_time:int=Field(...,gt=0,lt=120)
    ingredients:list[str]=Field(...,min_items=1)
    calories:Optional[int]=None
    is_vegetarian:bool=False
    is_spicy:bool=False
    

    @property
    def price_category(self):
        if self.price<10:
            return "Budget"
        elif self.price<25:
            return "Mid-range"
        else:
            return "Premium"
        
    @property
    def dietary_info(self):
        info=[]
        if self.is_vegetarian:
            info.append("Vegetarian")
        if self.is_spicy:
            info.append("Spicy")
        return info
    




    @validator("name")
    def name_must_be_alpha(cls, value):
        if not all(c.isalpha() or c.isspace() for c in value):
            raise ValueError("Name must contain only letters and spaces")
        return value 
    
    @validator("price")
    def price_within_range(cls, value):
        if value<1.00 or value>100.00:
            raise ValueError("Price must be between $1.00 and $100.00")
        return value
    
    @validator("ingredients")
    def must_have_ingredients(cls,value):
        if not value:
            raise ValueError("Ingredients are required")
        return value
    
    @validator("is_spicy")
    def desserts_and_beverages_cannot_be_spicy(cls,value,values):
        if "category" in values and value:
            if values["category"] in [FoodCategory.dessert,FoodCategory.beverage]:
                raise ValueError("Desserts and beverages cannot be spicy")
        return value
    
    @validator("calories")
    def calories_for_vegetarian(cls,value,values):
        if values.get("is_vegetarian") and (value is None or value>=800):
            raise ValueError("Vegetarian items must have calories < 800")
        return value
    

    @validator("preparation_time")
    def prep_time_for_beverages(cls,value,values):
        if "category" in values and values["category"]==FoodCategory.beverage and value>10:
            raise ValueError("Beverages must have preparation time <= 10 minutes")
        return value
    
class Customer(BaseModel):
    name:str=Field(...,min_length=3)
    contact: str=Field(...,min_length=10, max_length=15)

class OrderItem(BaseModel):
    item_id:int
    quantity:int=Field(...,gt=0)

    @validator("item_id")
    def must_exist_in_menu(cls,v):
        if v not in menu_db:
            raise ValueError("Item does not exist in menu")
        return v
    

class Order(BaseModel):
    order_id: str
    customer : Customer
    items:list[OrderItem]
    status: OrderStatus=OrderStatus.pending

    @property
    def total_price(self):
        total=Decimal(0)
        for order_item in self.items:
            food=menu_db[order_item.item_id]
            total+=food.price*order_item.quantity
        return total



class FoodItemResponse(BaseModel):
    id:int
    name:str
    category:FoodCategory
    price: Decimal
    is_available:bool


class OrderSummaryResponse(BaseModel):
    order_id:str
    customer_name:str 
    total_items:int 
    total_price:Decimal
    status:OrderStatus


class OrderResponse(BaseModel):
    order_id:str
    customer:Customer
    items: list[OrderItem]
    total_price:Decimal
    status:OrderStatus

class ErrorResponse(BaseModel):
    detail:str


@app.get("/")
def root():
    return {"message":"Welcome to the Restaurant Food Ordering System"}

@app.post("/menu",response_model=FoodItemResponse)
def create_menu_item(item:FoodItem):
    global menu_id_counter
    item.id=menu_id_counter
    menu_db[menu_id_counter]=item
    menu_id_counter+=1
    return item


@app.get("/menu",response_model=list[FoodItemResponse])
def get_menu():
    return list(menu_db.values())



@app.post("orders",response_model=OrderResponse, responses={400:{"model":ErrorResponse}})
def create_order(order_data:Order):
    if not order_data.items:
        raise HTTPException(status_code=400,detail="Order must have at least one item")
    orders_db[order_data.order_id]=order_data
    return OrderResponse(
        order_id=order_data.order_id,
        customer=order_data.customer,
        items=order_data.items,
        total_price=order_data.total_price,
        status=order_data.status
    )


@app.get("orders",response_model=list[OrderSummaryResponse])
def list_orders():
    return [
        OrderSummaryResponse(
            order_id=order.order_id,
            customer_name=order.customer.name,
            total_items=order.total_items,
            total_price=order.total_price,
            status=order.status
        )
        for order in orders_db.values()
    ]
    

@app.get("orders/{order_id}",response_model=OrderResponse,responses={404:{"model":ErrorResponse}})
def get_order(order_id:str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404,detail="Order not found")
    
    o=orders_db[order_id]
    return OrderResponse(
        order_id=o.order_id,
        customer=o.customer,
        items=o.items,
        total_price=o.total_price,
        status=o.status
    )

@app.put("orders/{order_id}/status",response_model=OrderResponse,responses={404:{"model":ErrorResponse}})
def update_order_status(order_id:str,status:OrderStatus):
    if order_id not in orders_db:
        raise HTTPException(status_code=404,detail="Order not found")
    orders_db[order_id].status=status
    o=orders_db[order_id]
    return OrderResponse(
        order_id=o.order_id,
        customer=o.customer,
        items=o.items,
        total_price=o.total_price,
        status=o.status
    )





if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)